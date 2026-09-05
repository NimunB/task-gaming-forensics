"""Jacobian-lens readout for Qwen3.5-9B, reimplemented against the reference (anthropics/jacobian-lens).

Why reimplemented: the official package requires transformers>=5.5; this project pins 5.2.0 and every
sampling script depends on that pin. The readout itself is small and fully specified by the reference:

    lens_l(h) = unembed(J_l @ h),   unembed(x) = lm_head(final_norm(x))        (jlens/lens.py, jlens/hf.py)

Conventions copied from the reference and checked against Step 1's hook cross-check:
  * "layer l residual" = output of `model.model.layers[l]` (forward hook, output[0]), which equals
    `output_hidden_states[l+1]` on this model (max abs diff 0.0, experiments/step1_smoke.json).
  * transport is `h @ J_l.T` (jlens/lens.py:transport); J_target (= layer 30 here) is the identity.
  * unembed casts to lm_head dtype and applies the model's own final RMSNorm, then lm_head.

Lens: camilablank/workspace-lenses qwen3.5-9b/j-lens/lens.pt — fit on Qwen/Qwen3.5-9B (instruct),
NeelNanda/pile-10k, n=25 prompts, target_layer 30, skip_first 4, standard estimator. n=25 is thin (the
reference README says ~100 prompts is "usable"); treat readouts as indicative and cross-check late
layers against the model's actual next-token logits.
"""
from __future__ import annotations
from pathlib import Path
import torch as t

ROOT = Path(__file__).resolve().parents[1]
LENS_PATH = ROOT / "experiments" / "lenses" / "qwen3.5-9b" / "j-lens" / "lens.pt"


class JLens:
    def __init__(self, path: Path = LENS_PATH, device="cuda:0", target_layer: int | None = None):
        d = t.load(path, map_location="cpu", weights_only=False)
        self.J = {int(l): m.to(device=device, dtype=t.float32) for l, m in d["J"].items()}
        self.source_layers = sorted(self.J)
        self.d_model = d["d_model"]; self.provenance = d.get("provenance", {})
        I = t.eye(self.d_model, device=device)
        dist = {l: ((self.J[l] - I).norm() / I.norm()).item() for l in self.source_layers}
        if target_layer is None:
            target_layer = int(self.provenance.get("target_layer", min(dist, key=dist.get)))
        self.target_layer = target_layer
        # The paper-faithful recipe stores J_target = I. Neuronpedia's gpt-oss-20b lens does not contain an
        # identity row (closest layer is still far from I), i.e. its target is the final block, which is not
        # stored. Record how far the anchor row is from I rather than assert; callers read it from .anchor_dist.
        self.anchor_dist = dist[self.target_layer]
        self.identity_anchor = self.anchor_dist < 1e-4

    def transport(self, h: t.Tensor, layer: int) -> t.Tensor:
        """h: [..., d_model] residual at `layer` (output of block `layer`) -> final-layer basis."""
        return h.float() @ self.J[layer].T


def unembed(model, x: t.Tensor) -> t.Tensor:
    """Reference unembed: lm_head(final_norm(x)) in lm_head dtype. Returns float32 logits."""
    head = model.lm_head; norm = model.model.norm
    x = x.to(dtype=head.weight.dtype, device=head.weight.device)
    return head(norm(x)).float()


@t.no_grad()
def readout(model, tok, input_ids: t.Tensor, lens: JLens, layers, positions, topk=10):
    """Run one forward pass; return, per (layer, position), the lens top-k tokens and the model's
    actual next-token top-1 at that position. `positions` index into the sequence (negatives ok).
    `layers` must be in lens.source_layers. Uses output_hidden_states: hidden_states[l+1] == block l output."""
    out = model(input_ids=input_ids, output_hidden_states=True)
    hs = out.hidden_states  # len n_layers+1; hs[l+1] is block l's output for l < n_layers-1.
    # NB: HF appends the FINAL-NORMED state as the last entry, so hs[-1] is post-norm; never re-unembed
    # it. The model's own logits come from out.logits. (Found by the unembed check in the smoke test:
    # re-unembedding hs[-1] gave max|Δlogit| = 5.4 and 8% argmax disagreement.)
    seq = input_ids.shape[1]; pos = [p % seq for p in positions]
    res = {}
    model_logits = out.logits[0, pos].float()
    model_top1 = model_logits.argmax(-1)
    for l in layers:
        h = hs[l + 1][0, pos]                    # block l output
        logits = unembed(model, lens.transport(h, l))
        top = logits.topk(topk, dim=-1)
        res[l] = {"top_tokens": [[tok.decode([i]) for i in row] for row in top.indices.tolist()],
                  "top_logits": top.values.tolist()}
    return res, [tok.decode([i]) for i in model_top1.tolist()], pos


@t.no_grad()
def token_rank(model, tok, input_ids: t.Tensor, lens: JLens, layer: int, position: int, target: str) -> int:
    """Rank (0 = top) of the single-token `target` in the lens readout at (layer, position)."""
    ids = tok(target, add_special_tokens=False)["input_ids"]
    assert len(ids) == 1, f"{target!r} is not a single token: {ids}"
    out = model(input_ids=input_ids, output_hidden_states=True)
    h = out.hidden_states[layer + 1][0, position % input_ids.shape[1]]
    logits = unembed(model, lens.transport(h, layer))
    return int((logits > logits[ids[0]]).sum().item())


@t.no_grad()
def rank_table(model, tok, input_ids: t.Tensor, lens: JLens, layers, position: int, targets: list[str], topk=8):
    """One forward pass; for each layer: lens top-k at `position` and the rank of each single-token target.
    Multi-token targets are skipped with rank None."""
    out = model(input_ids=input_ids, output_hidden_states=True)
    p = position % input_ids.shape[1]
    tids = {}
    for tg in targets:
        ids = tok(tg, add_special_tokens=False)["input_ids"]; tids[tg] = ids[0] if len(ids) == 1 else None
    rows = {}
    for l in layers:
        logits = unembed(model, lens.transport(out.hidden_states[l + 1][0, p], l))
        order = logits.argsort(descending=True)
        rank = {tg: (int((logits > logits[i]).sum().item()) if i is not None else None) for tg, i in tids.items()}
        rows[l] = {"top": [tok.decode([i]) for i in order[:topk].tolist()], "rank": rank}
    actual = tok.decode([int(out.logits[0, p].argmax())])
    return rows, actual


def find_span_positions(tok, input_ids: t.Tensor, substring: str) -> list[int]:
    """Token positions whose decoded prefix first covers `substring` — i.e. the tokens that spell it.
    Works on the decoded text of input_ids; returns the positions of the tokens overlapping the span."""
    ids = input_ids[0].tolist(); text = ""; starts = []
    for i in ids:
        starts.append(len(text)); text += tok.decode([i])
    k = text.find(substring)
    if k < 0: return []
    end = k + len(substring)
    return [p for p, s in enumerate(starts) if s < end and (starts[p + 1] if p + 1 < len(starts) else len(text)) > k]

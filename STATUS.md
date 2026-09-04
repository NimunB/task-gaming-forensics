# STATUS

## Where we are
- On the GPU box (Vast RTX PRO 6000 Blackwell Max-Q, 96 GB, driver 595.91.07, CUDA 12.8 in-image). Repo cloned, `vendor/` present at pinned commits. Step 3 approved and frozen.
- **Nothing installed, nothing downloaded.** Waiting on your approval for `scripts/BOX_SETUP.md` §2 and §3.
- Verified the box before asking, so the approval is for commands that will actually work: GPU is Blackwell (compute capability 12.0), which **requires cu128 or newer wheels** — the pinned `torch==2.11.0+cu128` is correct.
- Found one blocker in the §2 pin list: **`transformers==4.57.6` cannot load this model.** Details and the ask are under "Waiting on you". BOX_SETUP.md §2 itself says to ask before changing that pin, so this is the ask.
- Confirmed the model config from Hugging Face without downloading weights: 32 layers, hidden size 4096, 16 heads, head_dim 256, vocab 248320, bf16, `model_type: qwen3_5`, text decoder `qwen3_5_text`.

## What the numbers mean so far
- No experimental numbers. Only environment facts, N=1 box:
  - GPU 97,887 MiB free of VRAM; the 9B model in bf16 is ~18 GB, so probe extraction and sampling can run as two concurrent processes as the brief plans.
  - Disk: 99 GB free. Model download ~18 GB. Fits with room to spare.
  - Reading the transformers source at each release tag: the `qwen3_5` module is **absent** in v4.57.6, v4.58.0, v4.59.0, v4.60.0 and v5.0.0; **first present in v5.2.0**; latest is v5.16.1. This is a file-existence check on the released source tree, not a guess.

## Dumbest way this could be wrong
- **The transformers finding:** I checked for the existence of `src/transformers/models/qwen3_5/__init__.py` at each tag. If 4.57.6 supported the model under a different directory name, my conclusion is wrong. Cheap to disprove: the install would simply work. What would change my mind: `AutoModel.from_pretrained` succeeding on 4.57.6.
- **The Blackwell/cu128 claim:** taken from the instance manifest's `min_cuda_for_wheels: 12.8`, not measured. If wrong, the failure is loud and immediate (`no kernel image is available for execution on the device`), not silent.
- **The layer path** (`model.model.language_model.layers`) is read off the v5.2.0 source, not off a loaded model. Step 1 verifies it empirically before any hook is trusted.
- `/workspace` on this box is **not** a persistent volume (`workspace_is_volume: false`). Stop/start keeps it; recycle or destroy wipes it. Anything not pushed to GitHub is lost. This is a real risk, not a theoretical one.

## Decisions I made without asking
- Ran read-only inspection of the box (nvidia-smi, `pip list`, HTTP HEAD/GET of public config files on Hugging Face and GitHub). No installs, no downloads, no writes outside this repo. I judged that asking you to approve a command list I had not checked against the actual hardware would waste your time.
- Did **not** reuse the box's preinstalled `/venv/main` (it already has the exact `torch==2.11.0+cu128`). Reason: it carries `numpy 2.5.2`, while the thesis environment the probe code was audited in pins `numpy==1.26.4`. A fresh `.venv` per §2 reproduces the audited environment; the cost is re-downloading torch, a few minutes. Say the word if you would rather save the download.

## Waiting on you
**1. Approve `scripts/BOX_SETUP.md` §2 and §3 — with one pin change.**

§2 as written, verbatim:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
pip install transformers==4.57.6 accelerate==1.14.0 scikit-learn==1.9.0 numpy==1.26.4 pandas \
            einops==0.7.0 jaxtyping==0.2.38 PyYAML==6.0.3 python-dotenv==1.2.2 anthropic==0.116.0 \
            matplotlib==3.11.0 tqdm==4.68.4 pytest==8.3.4
pip install -e vendor/Probing-Safety-Behaviours
```
§3 as written, verbatim:
```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3.5-9B')"
```
The change I need approved: **`transformers==4.57.6` → `transformers==5.2.0`.** 4.57.6 has no `qwen3_5` model class, so `from_pretrained` will fail on the architecture; 5.2.0 is the earliest release that has it, so it is the smallest jump off the thesis pin. The thesis probe code touches only a small, stable slice of the transformers API (`AutoTokenizer`, `AutoModelForCausalLM`, `BitsAndBytesConfig`, `apply_chat_template`, `output_hidden_states`, `model.generate`), all of which survive the 5.x major bump — but a major-version bump is still a real risk and Step 1 is where it shows up. Alternative if you would rather not jump: switch to the Gemma 4 12B fallback, which 4.57.6 may also not know. I recommend 5.2.0.

**2. Nothing else is blocking.** Once you say go, I run §2 and §3, then Step 1 and Step 2 unattended, checkpointing after each, and stop at Gate 1 with `experiments/pilot_readable.md` ready for you.

## Next
1. On your approval: run §2 (with the transformers pin change), then §3 (~18 GB download, logged as not counted).
2. Step 1 smoke test (≤30 min): load bf16, locate the text decoder (expected `model.model.language_model.layers`, verified not assumed), hook one layer, extract thinking-token and answer-token activations separately, render all 10 tasks through the chat template and record prompt token counts and the exact thinking-tag offsets. Checkpoint.
3. Step 2 pilot (≤45 min): 5 impossible tasks x 3 samples at T=0.7, thinking on, seed 42, written to `experiments/pilot_readable.md` with a one-line agent guess per response. Checkpoint, then stop at Gate 1.

# Box setup — commands for Nimun to approve and run

Nothing in this file is run automatically. The agent does not install anything without asking.
Target: one 80 GB GPU (A100/H100) on RunPod or Vast, Ubuntu image with CUDA 12.8+ drivers.

## 1. Clone the project and the vendored repos (no installs)
```bash
git clone <this-repo-url> task-gaming-forensics && cd task-gaming-forensics
bash scripts/clone_vendor.sh
cp .env.example .env   # then fill HF_TOKEN (optional for Qwen; needed for Gemma fallback) and ANTHROPIC_API_KEY
```

## 2. Python environment (installs — approve first)
Pins follow vendor/Probing-Safety-Behaviours/requirements.txt where they matter for the probe code.
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
pip install transformers==4.57.6 accelerate==1.14.0 scikit-learn==1.9.0 numpy==1.26.4 pandas \
            einops==0.7.0 jaxtyping==0.2.38 PyYAML==6.0.3 python-dotenv==1.2.2 anthropic==0.116.0 \
            matplotlib==3.11.0 tqdm==4.68.4 pytest==8.3.4
pip install -e vendor/Probing-Safety-Behaviours
```
Not installed on purpose: bitsandbytes (bf16, no quantisation), datasets/fastapi/uvicorn/plotly/circuitsvis (thesis extras not used here).
If `transformers==4.57.6` does not know `Qwen3_5ForConditionalGeneration`, the fix is a newer transformers; ask before changing the pin.

## 3. Model weights (download — approve first)
```bash
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3.5-9B')"
```
About 18 GB in bf16.

## 4. Persistent Python process (recommended by Neel's doc; no installs)
```bash
tmux new -s lab
source .venv/bin/activate && ipython
```
The agent sends code with `tmux send-keys -t lab` and reads with `tmux capture-pane -p -t lab`.
Model and tokenizer are loaded once in that session; plots are saved as PNGs under experiments/figures/.

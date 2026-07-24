# Mac Local Image Generation

This setup runs the complete image-generation path on one Mac: Next.js on port 3000, FastAPI on port 8002, and a local Apple Silicon ComfyUI process on port 8188. No remote GPU server or SSH tunnel is required.

## Recommended Mac Configuration

- Apple Silicon MacBook Pro, including M4 with 16GB unified memory
- Existing `studio` Conda environment for AI Studio
- Existing ComfyUI installation at `/Users/lyj/WorkStation/Project/ComfyUI`
- Start SDXL Lightning at 768x768 or lower. Use SD1.5 as the faster development and fallback model.

## Install ComfyUI

```bash
mkdir -p /Users/lyj/WorkStation/Project
cd /Users/lyj/WorkStation/Project
git clone https://github.com/Comfy-Org/ComfyUI.git
cd ComfyUI

conda activate studio
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Confirm that PyTorch can use Metal Performance Shaders:

```bash
python - <<'PY'
import torch

print("torch:", torch.__version__)
print("MPS built:", torch.backends.mps.is_built())
print("MPS available:", torch.backends.mps.is_available())
PY
```

The expected MPS result is `True`. This installation and AI Studio both use the existing `studio` Conda environment.

## Install Checkpoints

Place both complete checkpoints in:

```text
/Users/lyj/WorkStation/Project/ComfyUI/models/checkpoints/
```

Expected layout:

```text
ComfyUI/
└── models/
    └── checkpoints/
        ├── v1-5-pruned-emaonly-fp16.safetensors
        └── sdxl_lightning_4step.safetensors
```

The SDXL Lightning file is the official all-in-one ComfyUI checkpoint from `ByteDance/SDXL-Lightning`, not the UNet-only or LoRA file:

```bash
hf download ByteDance/SDXL-Lightning sdxl_lightning_4step.safetensors \
  --local-dir /Users/lyj/WorkStation/Project/ComfyUI/models/checkpoints
```

The official model card requires the 4-step checkpoint to use 4 steps, Euler sampler, `sgm_uniform` scheduler, and CFG 1. AI Studio keeps these settings in its dedicated workflow template.

The current AI Studio SD1.5 mapping is `v1-5-pruned-emaonly-fp16.safetensors`. For a fresh download from the official Stable Diffusion 1.5 repository, use the upstream filename and update the environment mapping to match it exactly:

```bash
hf download stable-diffusion-v1-5/stable-diffusion-v1-5 \
  v1-5-pruned-emaonly.safetensors \
  --local-dir /Users/lyj/WorkStation/Project/ComfyUI/models/checkpoints
```

```dotenv
AI_STUDIO_SD15_CHECKPOINT=v1-5-pruned-emaonly.safetensors
```

Do not rename a partial download or commit model weights to the AI Studio repository.

## Configure AI Studio

Copy the canonical project example if a local file does not already exist:

```bash
cd /Users/lyj/WorkStation/Project/AI-Studio
cp .env.example .env
```

Relevant values:

```dotenv
COMFYUI_BASE_URL=http://127.0.0.1:8188
AI_STUDIO_DEFAULT_IMAGE_MODEL=sd15
AI_STUDIO_SD15_CHECKPOINT=v1-5-pruned-emaonly-fp16.safetensors
AI_STUDIO_SDXL_LIGHTNING_CHECKPOINT=sdxl_lightning_4step.safetensors
```

`AI_STUDIO_COMFYUI_BASE_URL` is temporarily accepted for migration but is deprecated. Use only `COMFYUI_BASE_URL` for new configurations. `AI_STUDIO_COMFYUI_OUTPUT_DIR` is ignored by the image path: FastAPI downloads results through the ComfyUI `/view` API.

## Start Local ComfyUI

```bash
conda activate studio
cd /Users/lyj/WorkStation/Project/ComfyUI
python main.py --listen 127.0.0.1 --port 8188
```

Check connectivity before starting AI Studio:

```bash
curl --fail http://127.0.0.1:8188/system_stats
```

## Start AI Studio

The Mac startup script reuses a healthy ComfyUI process. If port 8188 is free, it starts ComfyUI from the standard directory and waits for `/system_stats` before starting FastAPI and Next.js:

```bash
cd /Users/lyj/WorkStation/Project/AI-Studio
bash scripts/start-mac-dev.sh
```

Open:

- Frontend: `http://127.0.0.1:3000/images`
- FastAPI docs: `http://127.0.0.1:8002/docs`

If ports 3000 or 8002 are occupied, the script stops without terminating the unknown process. Press Ctrl+C to stop only the services started by this script. A ComfyUI process that was already running remains untouched.

To stop a manually started ComfyUI process, return to its terminal and press Ctrl+C.

## Troubleshooting

### Errno 61 Connection refused

Nothing is accepting connections on port 8188. Run `bash scripts/start-mac-dev.sh` to start the standard local installation, or start ComfyUI manually and rerun the `/system_stats` check.

### Checkpoint not found

Confirm the configured filename exactly matches the name returned by ComfyUI and the file is under `models/checkpoints`. Restart or refresh ComfyUI after adding a checkpoint.

### MPS out of memory

Close other memory-intensive applications, start with 512x512 or 768x768, keep batch size at 1, and use SD1.5 when SDXL exceeds available unified memory.

### First generation is slow

The first request must load model weights. Later requests may be faster, but no fixed generation time is guaranteed.

### 1024x1024 causes memory pressure

Use 768x768 or a lower resolution for SDXL Lightning on a 16GB Mac. SD1.5 remains the recommended quick-development model.

## References

- [ByteDance SDXL-Lightning model card](https://huggingface.co/ByteDance/SDXL-Lightning)
- [ComfyUI repository](https://github.com/Comfy-Org/ComfyUI)

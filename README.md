# AI Studio

AI Studio 是一个企业级 AIGC 应用平台项目，目标是沉淀可扩展、可维护的 AI 应用工程能力。第一阶段只完成 FastAPI 后端初始化，为后续 AI Chat、AI Image、Face Swap、Prompt Library、Model Manager、History 和 Docker Deployment 打基础。

## 技术栈

- Backend: FastAPI, Pydantic Settings, Uvicorn
- AI: ComfyUI, Stable Diffusion, FaceFusion, InsightFace, OpenAI SDK, Qwen API
- Frontend: Vue 3
- Deployment: Docker, Docker Compose

当前阶段只启用 FastAPI。

## 项目目录

```text
AI-Studio/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── utils/
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
├── data/uploads/
├── data/outputs/
├── docker/
├── docs/
├── frontend/
├── prompts/
├── scripts/
├── workflows/
├── docker-compose.yml
└── README.md
```

## 快速启动

```bash
conda activate df
cd /3241903007/workstation/LYJ/AI-Studio/backend
pip install -r requirements-dev.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8001/api/v1/health
```

预期返回：

```json
{"status":"ok"}
```

Swagger 文档：

```text
http://127.0.0.1:8001/docs
```

## Docker 启动

```bash
docker compose up --build
```

服务会映射到宿主机 `8001` 端口。

## Roadmap

- Phase 1: FastAPI 项目初始化、统一配置、统一路由、健康检查、Docker 基础配置
- Phase 2: AI Chat 模块，接入 GPT/Qwen/Claude
- Phase 3: Prompt Library 与 History
- Phase 4: Stable Diffusion / ComfyUI 图像生成
- Phase 5: FaceFusion / InsightFace 换脸能力
- Phase 6: Model Manager 与企业级 Docker 部署

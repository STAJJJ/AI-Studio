# AI Studio Demo Script

## 1. Home And Workspace Sidebar

Open `http://127.0.0.1:3000`.

Show the Workspace Sidebar, primary navigation, runtime card, and Recent Workflows section. Explain that the app is organized around AI workflows rather than isolated demo pages.

## 2. AI Chat

Open `AI Chat`.

Select `AIGC Engineer`, send a short question, and point out real streaming output through the FastAPI LLM Gateway. Mention that provider endpoint IDs and API keys stay in backend configuration.

## 3. Text To Image

Open `Text to Image`.

Select `Stable Diffusion 1.5`, enter a prompt, generate an image, and show polling, preview, and download. Explain that models and workflow templates are selected through the backend registry.

## 4. Face Swap

Open `Face Swap`.

Upload one source face and one target image. Start the task, wait for polling to complete, then preview and download the result. Explain that FaceFusion is isolated behind an executor boundary.

## 5. Workflow History

Open `Workflow History`.

Show image generation and face swap records, filters, detail view, result preview, and download. Click a Recent Workflow from the Sidebar to show `/history?run_id=...` deep-link behavior.

## 6. SQLite Persistence

Stop and restart the backend.

Open History again and show that workflow records remain available because metadata is stored in SQLite.

## 7. Project Structure And Tests

Show the repository structure:

- `backend/app/api/v1/endpoints`
- `backend/app/services`
- `backend/app/services/comfyui`
- `backend/app/services/llm`
- `frontend/app`
- `frontend/components`
- `scripts`

Run or show the output of:

```bash
./scripts/check.sh
```

Close by emphasizing Router / Service / Executor / Registry layering and local runtime isolation.

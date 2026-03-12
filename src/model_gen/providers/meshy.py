"""Meshy provider - AI 3D model generation."""

from __future__ import annotations

import httpx
from . import BaseProvider, ModelResult

API_BASE = "https://api.meshy.ai/openapi"


class MeshyProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "meshy"

    @property
    def description(self) -> str:
        return "Meshy (Meshy-6) - High quality AI 3D model generation with PBR textures (GLB/FBX/OBJ/USDZ)"

    @property
    def free_tier_info(self) -> str:
        return "100 credits/month free (~5 models, text-to-3D costs 5-20 credits)"

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        output_format: str = "glb",
    ) -> ModelResult:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            if image_url:
                # Image-to-3D (v1 API)
                body = {
                    "image_url": image_url,
                    "ai_model": "meshy-6",
                    "topology": "triangle",
                    "should_remesh": True,
                }
                resp = await client.post(
                    f"{API_BASE}/v1/image-to-3d",
                    headers=headers,
                    json=body,
                )
            else:
                # Text-to-3D preview (v2 API)
                body = {
                    "mode": "preview",
                    "prompt": prompt,
                    "ai_model": "meshy-6",
                    "topology": "triangle",
                    "should_remesh": True,
                }
                resp = await client.post(
                    f"{API_BASE}/v2/text-to-3d",
                    headers=headers,
                    json=body,
                )

            if resp.status_code >= 400:
                try:
                    err = resp.json()
                    msg = err.get("message", f"HTTP {resp.status_code}")
                except Exception:
                    msg = f"HTTP {resp.status_code}"
                return ModelResult(status="failed", error=msg)

            data = resp.json()
            task_id = data.get("result", "")
            # Store whether this was image-to-3d in task_id prefix for query routing
            if image_url:
                task_id = f"img:{task_id}"

            return ModelResult(task_id=task_id, status="processing")

    async def query(self, task_id: str) -> ModelResult:
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Route to correct endpoint based on task type
        if task_id.startswith("img:"):
            real_id = task_id[4:]
            url = f"{API_BASE}/v1/image-to-3d/{real_id}"
        else:
            real_id = task_id
            url = f"{API_BASE}/v2/text-to-3d/{real_id}"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(url, headers=headers)

            if resp.status_code >= 400:
                return ModelResult(
                    task_id=task_id,
                    status="failed",
                    error=f"HTTP {resp.status_code}",
                )

            data = resp.json()
            status = data.get("status", "")

            if status == "SUCCEEDED":
                model_urls_raw = data.get("model_urls", {})
                model_urls = {k: v for k, v in model_urls_raw.items() if v}
                primary = model_urls.get("glb", "")
                thumbnail = data.get("thumbnail_url", "")
                return ModelResult(
                    task_id=task_id,
                    status="success",
                    model_url=primary,
                    model_urls=model_urls,
                    thumbnail_url=thumbnail,
                )
            elif status == "FAILED":
                err = data.get("task_error", {})
                msg = err.get("message", "Generation failed") if isinstance(err, dict) else str(err)
                return ModelResult(
                    task_id=task_id,
                    status="failed",
                    error=msg,
                )
            else:
                progress = data.get("progress", 0)
                return ModelResult(
                    task_id=task_id,
                    status="processing",
                    error=f"Status: {status}, Progress: {progress}%",
                )

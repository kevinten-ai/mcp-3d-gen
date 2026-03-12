"""Tripo3D provider - AI 3D model generation."""

from __future__ import annotations

import httpx
from . import BaseProvider, ModelResult

API_BASE = "https://api.tripo3d.ai/v2/openapi"


class TripoProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "tripo"

    @property
    def description(self) -> str:
        return "Tripo3D v2.5 - Fast AI 3D model generation from text or images (GLB/FBX/OBJ)"

    @property
    def free_tier_info(self) -> str:
        return "300 credits/month free (Basic plan, ~10 models)"

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        output_format: str = "glb",
    ) -> ModelResult:
        if image_url:
            body = {
                "type": "image_to_model",
                "file": {"type": "jpg", "url": image_url},
                "model_version": "v2.5-20250123",
            }
        else:
            body = {
                "type": "text_to_model",
                "prompt": prompt,
                "model_version": "v2.5-20250123",
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{API_BASE}/task",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            data = resp.json()

            if data.get("code") != 0:
                return ModelResult(
                    status="failed",
                    error=data.get("message", f"HTTP {resp.status_code}"),
                )

            task_id = data.get("data", {}).get("task_id", "")
            return ModelResult(task_id=task_id, status="processing")

    async def query(self, task_id: str) -> ModelResult:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(
                f"{API_BASE}/task/{task_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            data = resp.json()

            if data.get("code") != 0:
                return ModelResult(
                    task_id=task_id,
                    status="failed",
                    error=data.get("message", "Query failed"),
                )

            task_data = data.get("data", {})
            status = task_data.get("status", "")

            if status == "success":
                output = task_data.get("output", {})
                model_url = output.get("model", "")
                rendered_image = output.get("rendered_image", "")
                return ModelResult(
                    task_id=task_id,
                    status="success",
                    model_url=model_url,
                    model_urls={"glb": model_url} if model_url else {},
                    thumbnail_url=rendered_image,
                )
            elif status in ("failed",):
                return ModelResult(
                    task_id=task_id,
                    status="failed",
                    error=task_data.get("message", "Generation failed"),
                )
            else:
                progress = task_data.get("progress", 0)
                return ModelResult(
                    task_id=task_id,
                    status="processing",
                    error=f"Progress: {progress}%",
                )

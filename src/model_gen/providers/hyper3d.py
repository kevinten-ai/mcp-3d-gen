"""Hyper3D Rodin provider - AI 3D model generation."""

from __future__ import annotations

import httpx
from . import BaseProvider, ModelResult

API_BASE = "https://api.hyper3d.com/api/v2"


class Hyper3DProvider(BaseProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key

    @property
    def name(self) -> str:
        return "hyper3d"

    @property
    def description(self) -> str:
        return "Hyper3D Rodin - High quality AI 3D model generation with PBR textures (GLB/FBX/OBJ/USDZ/STL)"

    @property
    def free_tier_info(self) -> str:
        return "Free credits on signup (~10 models). $0.5 credits/model after."

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        output_format: str = "glb",
    ) -> ModelResult:
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # Rodin uses multipart/form-data
        data = {
            "tier": "Regular",
            "geometry_file_format": output_format,
            "material": "PBR",
            "quality": "medium",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            if image_url:
                # Image-to-3D: download image first, then upload
                try:
                    img_resp = await client.get(image_url, timeout=30.0)
                    if img_resp.status_code != 200:
                        return ModelResult(status="failed", error=f"Failed to download image: HTTP {img_resp.status_code}")
                    image_bytes = img_resp.content
                except Exception as e:
                    return ModelResult(status="failed", error=f"Failed to download image: {e}")

                files = {"images": ("image.png", image_bytes, "image/png")}
                if prompt:
                    data["prompt"] = prompt
            else:
                # Text-to-3D: no images, prompt required
                files = {}
                data["prompt"] = prompt

            resp = await client.post(
                f"{API_BASE}/rodin",
                headers=headers,
                data=data,
                files=files if files else None,
                timeout=60.0,
            )

            try:
                result = resp.json()
            except Exception:
                return ModelResult(status="failed", error=f"HTTP {resp.status_code}")

            if result.get("error"):
                return ModelResult(status="failed", error=result["error"])

            task_uuid = result.get("uuid", "")
            sub_key = result.get("jobs", {}).get("subscription_key", "")

            if not task_uuid or not sub_key:
                return ModelResult(status="failed", error="No task UUID or subscription key returned")

            # Store both IDs: uuid for download, subscription_key for status
            # Format: "uuid|subscription_key"
            combined_id = f"{task_uuid}|{sub_key}"
            return ModelResult(task_id=combined_id, status="processing")

    async def query(self, task_id: str) -> ModelResult:
        # Parse combined ID
        parts = task_id.split("|", 1)
        if len(parts) != 2:
            return ModelResult(task_id=task_id, status="failed", error="Invalid task ID format")

        task_uuid, sub_key = parts
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Check status using subscription_key
            status_resp = await client.post(
                f"{API_BASE}/status",
                headers=headers,
                json={"subscription_key": sub_key},
            )

            try:
                status_data = status_resp.json()
            except Exception:
                return ModelResult(task_id=task_id, status="failed", error=f"HTTP {status_resp.status_code}")

            if status_data.get("error"):
                return ModelResult(task_id=task_id, status="failed", error=status_data["error"])

            # Parse status - response format: {"jobs": [{"uuid": "...", "status": "..."}]}
            # or {"jobs": {"uuid": "status"}} - handle both
            jobs = status_data.get("jobs", [])

            # Determine overall status
            all_done = True
            any_failed = False
            current_status = "processing"

            if isinstance(jobs, list):
                for job in jobs:
                    if isinstance(job, dict):
                        s = job.get("status", "")
                    else:
                        s = str(job)
                    if s == "Failed":
                        any_failed = True
                    if s != "Done":
                        all_done = False
            elif isinstance(jobs, dict):
                for uid, s in jobs.items():
                    if s == "Failed":
                        any_failed = True
                    if s != "Done":
                        all_done = False

            if any_failed:
                return ModelResult(task_id=task_id, status="failed", error="Generation failed")

            if not all_done:
                return ModelResult(task_id=task_id, status="processing", error="Still generating...")

            # All done - download results using task_uuid
            dl_resp = await client.post(
                f"{API_BASE}/download",
                headers=headers,
                json={"task_uuid": task_uuid},
            )

            try:
                dl_data = dl_resp.json()
            except Exception:
                return ModelResult(task_id=task_id, status="failed", error=f"Download HTTP {dl_resp.status_code}")

            if dl_data.get("error"):
                return ModelResult(task_id=task_id, status="failed", error=dl_data["error"])

            file_list = dl_data.get("list", [])
            model_urls = {}
            thumbnail_url = ""
            primary_url = ""

            for item in file_list:
                name = item.get("name", "")
                url = item.get("url", "")
                if not url:
                    continue

                # Categorize files by extension
                name_lower = name.lower()
                if name_lower.endswith(".glb"):
                    model_urls["glb"] = url
                    if not primary_url:
                        primary_url = url
                elif name_lower.endswith(".fbx"):
                    model_urls["fbx"] = url
                elif name_lower.endswith(".obj"):
                    model_urls["obj"] = url
                elif name_lower.endswith(".usdz"):
                    model_urls["usdz"] = url
                elif name_lower.endswith(".stl"):
                    model_urls["stl"] = url
                elif name_lower.endswith((".webp", ".png", ".jpg")):
                    thumbnail_url = url

            if not primary_url and model_urls:
                primary_url = next(iter(model_urls.values()))

            return ModelResult(
                task_id=task_id,
                status="success",
                model_url=primary_url,
                model_urls=model_urls,
                thumbnail_url=thumbnail_url,
            )

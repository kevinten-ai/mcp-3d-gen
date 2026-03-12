from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path

import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

from .providers import (
    register_provider,
    get_provider,
    list_providers as get_all_providers,
)
from .providers.tripo import TripoProvider
from .providers.meshy import MeshyProvider

MODEL_OUTPUT_DIR = os.getenv("MODEL_OUTPUT_DIR", os.path.join(os.getcwd(), "output"))

server = Server("mcp-3d-gen")


def _init_providers() -> None:
    """Register providers based on available environment variables."""
    tripo_key = os.getenv("TRIPO_API_KEY", "")
    if tripo_key:
        register_provider(TripoProvider(tripo_key))

    meshy_key = os.getenv("MESHY_API_KEY", "")
    if meshy_key:
        register_provider(MeshyProvider(meshy_key))


_init_providers()


def _default_provider_name() -> str | None:
    providers = get_all_providers()
    for name in ("tripo", "meshy"):
        if name in providers:
            return name
    return None


async def _try_download(url: str, output_dir: str, prefix: str, ext: str = "glb") -> str | None:
    """Try to download file to local disk."""
    try:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = out / f"{prefix}_{timestamp}.{ext}"
        async with httpx.AsyncClient(verify=False, follow_redirects=True) as client:
            resp = await client.get(url, timeout=120.0)
            if resp.status_code == 200 and len(resp.content) > 0:
                filepath.write_bytes(resp.content)
                return str(filepath)
    except Exception:
        pass
    return None


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    providers = get_all_providers()
    provider_names = list(providers.keys())
    default = _default_provider_name()

    return [
        types.Tool(
            name="generate_3d",
            description=f"Generate a 3D model from text or image. Available providers: {', '.join(provider_names) or 'none configured'}. Default: {default or 'none'}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Text description of the 3D model to generate",
                    },
                    "image_url": {
                        "type": "string",
                        "description": "Image URL for image-to-3D generation. If provided, generates 3D model from this image. Optional.",
                    },
                    "provider": {
                        "type": "string",
                        "description": f"Provider to use: {', '.join(provider_names)}. Default: {default}",
                        "enum": provider_names if provider_names else ["none"],
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Output format: glb, fbx, obj, usdz. Default: glb",
                        "default": "glb",
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "Directory to save 3D model. Optional.",
                    },
                },
                "required": ["prompt"],
            },
        ),
        types.Tool(
            name="query_3d_status",
            description="Query the status of a 3D model generation task and download the result.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "Task ID returned by generate_3d",
                    },
                    "provider": {
                        "type": "string",
                        "description": f"Provider that was used: {', '.join(provider_names)}",
                        "enum": provider_names if provider_names else ["none"],
                    },
                    "output_format": {
                        "type": "string",
                        "description": "Preferred download format: glb, fbx, obj, usdz. Default: glb",
                        "default": "glb",
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "Directory to save 3D model. Optional.",
                    },
                },
                "required": ["task_id", "provider"],
            },
        ),
        types.Tool(
            name="list_providers",
            description="List all available 3D model generation providers.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if not arguments:
        arguments = {}

    if name == "list_providers":
        providers = get_all_providers()
        if not providers:
            return [types.TextContent(type="text", text="No providers configured. Set TRIPO_API_KEY or MESHY_API_KEY.")]
        lines = ["**3D Model Generation Providers:**"]
        for p in providers.values():
            lines.append(f"  **{p.name}** - {p.description}\n    Free tier: {p.free_tier_info}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    if name == "generate_3d":
        prompt = arguments.get("prompt")
        if not prompt:
            return [types.TextContent(type="text", text="Missing prompt")]

        provider_name = arguments.get("provider") or _default_provider_name()
        if not provider_name:
            return [types.TextContent(type="text", text="No providers configured. Set TRIPO_API_KEY or MESHY_API_KEY.")]

        provider = get_provider(provider_name)
        if not provider:
            available = ", ".join(get_all_providers().keys())
            return [types.TextContent(type="text", text=f"Unknown provider: {provider_name}. Available: {available}")]

        image_url = arguments.get("image_url")
        output_format = arguments.get("output_format", "glb")

        mode = "image-to-3D" if image_url else "text-to-3D"
        result = await provider.generate(prompt, image_url=image_url, output_format=output_format)

        if result.status == "failed":
            return [types.TextContent(type="text", text=f"Failed: {result.error}")]

        return [types.TextContent(
            type="text",
            text=f"3D model generation submitted via **{provider_name}** ({mode}).\nTask ID: `{result.task_id}`\nUse `query_3d_status` with task_id=`{result.task_id}` and provider=`{provider_name}` to check status.",
        )]

    if name == "query_3d_status":
        task_id = arguments.get("task_id")
        provider_name = arguments.get("provider")
        if not task_id or not provider_name:
            return [types.TextContent(type="text", text="Missing task_id or provider")]

        provider = get_provider(provider_name)
        if not provider:
            return [types.TextContent(type="text", text=f"Unknown provider: {provider_name}")]

        result = await provider.query(task_id)

        if result.status == "processing":
            info = result.error or "in progress"
            return [types.TextContent(type="text", text=f"Still processing ({info}). Try again in 10-30 seconds.")]

        if result.status == "failed":
            return [types.TextContent(type="text", text=f"Failed: {result.error}")]

        # Success
        output_format = arguments.get("output_format", "glb")
        output_dir = arguments.get("output_directory") or MODEL_OUTPUT_DIR

        results = []

        # Show available formats
        if result.model_urls:
            fmt_list = ", ".join(result.model_urls.keys())
            results.append(types.TextContent(type="text", text=f"3D model ready! Available formats: {fmt_list}"))

        # Pick best download URL
        download_url = result.model_urls.get(output_format) or result.model_url
        if download_url:
            results.append(types.TextContent(type="text", text=f"Download URL ({output_format}): {download_url}"))
            filepath = await _try_download(download_url, output_dir, provider_name, ext=output_format)
            if filepath:
                results.append(types.TextContent(type="text", text=f"Downloaded to: {filepath}"))
            else:
                results.append(types.TextContent(type="text", text="Auto-download failed. Use the URL above to download manually."))

        if result.thumbnail_url:
            results.append(types.TextContent(type="text", text=f"Thumbnail: {result.thumbnail_url}"))

        # Show all format URLs
        if result.model_urls and len(result.model_urls) > 1:
            lines = ["Other formats:"]
            for fmt, url in result.model_urls.items():
                if fmt != output_format:
                    lines.append(f"  {fmt}: {url}")
            results.append(types.TextContent(type="text", text="\n".join(lines)))

        return results or [types.TextContent(type="text", text="Model ready but no download URL available.")]

    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-3d-gen",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())

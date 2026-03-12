# mcp-3d-gen

Multi-provider AI 3D model generation MCP server, focused on free-tier models.

## Supported Providers

| Provider | Model | Free Tier | Output Formats |
|---|---|---|---|
| **Tripo3D** | v2.5 | 300 credits/month (~10 models) | GLB/FBX/OBJ |
| **Meshy** | Meshy-6 | 100 credits/month (~5 models) | GLB/FBX/OBJ/USDZ |

## Installation

### Claude Code (Global)

```bash
claude mcp add -s user mcp-3d-gen \
  --env TRIPO_API_KEY=your_key \
  --env MESHY_API_KEY=your_key \
  -- uv --directory /path/to/mcp-3d-gen run model-gen
```

Only configure the providers you want to use. At least one API key is required.

## API Key Registration Guide

### 1. Tripo3D — 300 Credits/Month Free

| Item | Detail |
|---|---|
| Platform | Tripo3D |
| URL | https://www.tripo3d.ai |
| Free Tier | **300 credits/month (Basic plan, ~10 models)** |
| Env Var | `TRIPO_API_KEY` |

**Steps:**
1. Visit https://www.tripo3d.ai and sign up
2. Go to API Platform: https://platform.tripo3d.ai
3. Navigate to **API Keys** and create a new key
4. Copy the key (format: `tsk_xxxxxxxxxxxxxxxx`)

> Free plan includes 300 credits/month, 1 concurrent task, and public outputs (CC BY 4.0). Text-to-3D costs ~30 credits/model.

---

### 2. Meshy — 100 Credits/Month Free

| Item | Detail |
|---|---|
| Platform | Meshy |
| URL | https://www.meshy.ai |
| Free Tier | **100 credits/month (text-to-3D costs 5-20 credits)** |
| Env Var | `MESHY_API_KEY` |

**Steps:**
1. Visit https://www.meshy.ai and sign up
2. Go to API Settings: https://www.meshy.ai/api
3. Create an API key
4. Copy the key (format: `msy_xxxxxxxxxxxxxxxx`)

> Free plan has 10 downloads/month and lower priority queue. API access may require Pro plan ($10/month).

---

## Environment Variables

| Variable | Provider | Required |
|---|---|---|
| `TRIPO_API_KEY` | Tripo3D | At least one |
| `MESHY_API_KEY` | Meshy | must be configured |
| `MODEL_OUTPUT_DIR` | Output path | Optional, default: `./output` |

## Tools

- **generate_3d** — Generate a 3D model from text or image. Params: `prompt`, `image_url` (optional, for image-to-3D), `provider`, `output_format`.
- **query_3d_status** — Check generation status and download the result.
- **list_providers** — Show all available providers and their free tier info.

## Architecture

```
src/model_gen/
├── __init__.py
├── server.py              # MCP server + tool definitions
└── providers/
    ├── __init__.py        # BaseProvider + registry
    ├── tripo.py           # Tripo3D
    └── meshy.py           # Meshy
```

### Adding a New Provider

1. Create a new file under `src/model_gen/providers/`
2. Implement the `BaseProvider` abstract class with `generate()` and `query()` methods
3. Register it in `server.py:_init_providers()` with an env var check

## Related Projects

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — AI video, speech & music generation MCP server
- [mcp-image-gen](https://github.com/kevinten-ai/mcp-image-gen) — AI image generation MCP server

## License

MIT

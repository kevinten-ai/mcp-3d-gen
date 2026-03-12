# mcp-3d-gen

多平台 AI 3D 模型生成 MCP 服务器，专注于免费额度模型。

## 支持的平台

| 平台 | 模型 | 免费额度 | 输出格式 |
|---|---|---|---|
| **Tripo3D** | v2.5 | 每月300积分（约10个模型） | GLB/FBX/OBJ |
| **Meshy** | Meshy-6 | 每月100积分（约5个模型） | GLB/FBX/OBJ/USDZ |

## 安装

### Claude Code 全局配置

```bash
claude mcp add -s user mcp-3d-gen \
  --env TRIPO_API_KEY=你的key \
  --env MESHY_API_KEY=你的key \
  -- uv --directory /path/to/mcp-3d-gen run model-gen
```

只需配置你要使用的平台，至少配置一个。

## API Key 注册指南

### 1. Tripo3D — 每月300积分免费

| 项目 | 详情 |
|---|---|
| 平台 | Tripo3D |
| 地址 | https://www.tripo3d.ai |
| 免费额度 | **每月300积分（Basic 计划，约10个模型）** |
| 环境变量 | `TRIPO_API_KEY` |

**注册步骤：**
1. 访问 https://www.tripo3d.ai 注册
2. 进入 API 平台：https://platform.tripo3d.ai
3. 在 **API Keys** 页面创建新 Key
4. 复制 Key（格式：`tsk_xxxxxxxxxxxxxxxx`）

> 免费计划每月300积分，1个并发任务，输出为公开（CC BY 4.0）。文字生3D约消耗30积分/个。

---

### 2. Meshy — 每月100积分免费

| 项目 | 详情 |
|---|---|
| 平台 | Meshy |
| 地址 | https://www.meshy.ai |
| 免费额度 | **每月100积分（文字生3D消耗5-20积分）** |
| 环境变量 | `MESHY_API_KEY` |

**注册步骤：**
1. 访问 https://www.meshy.ai 注册
2. 进入 API 设置：https://www.meshy.ai/api
3. 创建 API Key
4. 复制 Key（格式：`msy_xxxxxxxxxxxxxxxx`）

> 免费计划每月10次下载，低优先级队列。API 访问可能需要 Pro 计划（$10/月）。

---

## 环境变量汇总

| 变量 | 平台 | 说明 |
|---|---|---|
| `TRIPO_API_KEY` | Tripo3D | 至少配置 |
| `MESHY_API_KEY` | Meshy | 一个平台 |
| `MODEL_OUTPUT_DIR` | 输出目录 | 可选，默认 `./output` |

## 工具说明

- **generate_3d** — 根据文字或图片生成3D模型。参数：`prompt`（描述）、`image_url`（可选，图片转3D）、`provider`（平台）、`output_format`（格式）。
- **query_3d_status** — 查询生成状态，完成后自动下载。
- **list_providers** — 列出所有可用平台及其免费额度信息。

## 项目结构

```
src/model_gen/
├── __init__.py
├── server.py              # MCP 服务器 + 工具定义
└── providers/
    ├── __init__.py        # Provider 基类 + 注册机制
    ├── tripo.py           # Tripo3D
    └── meshy.py           # Meshy
```

### 添加新平台

1. 在 `src/model_gen/providers/` 下创建新文件
2. 实现 `BaseProvider` 抽象类的 `generate()` 和 `query()` 方法
3. 在 `server.py:_init_providers()` 中注册，通过环境变量控制启用

## 相关项目

- [mcp-video-gen](https://github.com/kevinten-ai/mcp-video-gen) — AI 视频、语音、音乐生成 MCP 服务器
- [mcp-image-gen](https://github.com/kevinten-ai/mcp-image-gen) — AI 图片生成 MCP 服务器

## 许可证

MIT

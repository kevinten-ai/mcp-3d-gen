# mcp-3d-gen

多平台 AI 3D 模型生成 MCP 服务器，专注于免费额度模型。

## 支持的平台

| 平台 | 模型 | 免费额度 | 输出格式 |
|---|---|---|---|
| **Tripo3D** | v2.5 | 每月300积分（约10个模型） | GLB/FBX/OBJ |
| **Meshy** | Meshy-6 | API 需 Pro 计划（$10/月，1000积分） | GLB/FBX/OBJ/USDZ |

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

### 1. Tripo3D — 每月300积分免费（Studio）

| 项目 | 详情 |
|---|---|
| 平台 | Tripo3D |
| 官网 | https://www.tripo3d.ai |
| API 平台 | https://platform.tripo3d.ai |
| 免费额度 | **Basic 计划：每月300积分（约10个模型），1个并发任务** |
| 环境变量 | `TRIPO_API_KEY` |

**注册步骤：**
1. 访问 https://www.tripo3d.ai ，点击 **Sign Up**（支持邮箱或 Google 账号）
2. 登录后，进入 **API 平台**：https://platform.tripo3d.ai
3. 进入 **API Keys** 页面：https://platform.tripo3d.ai/api-keys
4. 点击 **Create API Key** 创建新 Key
5. 复制 Key（格式：`tsk_xxxxxxxxxxxxxxxx`）

> **价格：** Basic 计划免费，每月300积分。文字生3D约30积分/个。免费输出为公开模型（CC BY 4.0）。付费计划：Professional（$11.94/月，3000积分）、Advanced（$29.94/月，8000积分）。

> **注意：** API 平台（platform.tripo3d.ai）与 Studio 网页端共用登录账号，但积分池独立。

---

### 2. Meshy — 每月100积分免费（API 需 Pro 计划）

| 项目 | 详情 |
|---|---|
| 平台 | Meshy |
| 官网 | https://www.meshy.ai |
| API 设置 | https://www.meshy.ai/settings/api |
| 免费额度 | **免费计划100积分/月，但 API 访问需 Pro 计划（$10/月起）** |
| 环境变量 | `MESHY_API_KEY` |

**注册步骤：**
1. 访问 https://www.meshy.ai ，点击 **Sign Up**（支持邮箱、Google、Apple）
2. 登录后，进入 **Settings** > **API**：https://www.meshy.ai/settings/api
3. 点击 **Create API Key** 创建新 Key
4. 复制 Key（格式：`msy_xxxxxxxxxxxxxxxx`）
5. 免费用户可使用 **测试模式 Key** `msy_dummy_api_key_for_test_mode_12345678` 来体验接口（不消耗积分，返回测试数据）

> **价格：** 免费计划有100积分/月但**无 API 访问权限**（仅网页端）。Pro 计划（$10-20/月）解锁 API，1000积分。文字生3D消耗5-20积分/个。Studio 计划（$48-60/月）有4000积分。

> **重要提示：** API 访问是 Pro 及以上计划的功能。免费用户只能通过网页端生成。如需免费 API 访问，建议优先使用 Tripo3D。

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

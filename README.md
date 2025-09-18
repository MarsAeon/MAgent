# MAgent - 多智能体概念优化引擎（Python + React + Eel）

MAgent 用多个角色化智能体（澄清、创新、批判、综合、验证、总结）对输入想法进行多轮推理与协作，帮助从粗糙创意逐步收敛到可执行方案。

- 平台：Windows / macOS / Linux
- 许可证：MIT

## 技术栈

- 后端：Python 3.11+ · Eel · Pydantic · Loguru
- 前端：React 18 + TypeScript + Vite + Tailwind CSS
- 运行方式：Vite 产出静态资源，由 Eel 提供本地 WebView 与后端 API

## 项目结构

```
MAgent/
├─ main.py                    # 应用入口（Eel 初始化、API 暴露）
├─ start.py                   # 交互式启动脚本（开发/生产/纯后端）
├─ start_production.py        # 生产启动脚本（自动构建并启动）
├─ requirements.txt           # Python 依赖
├─ package.json               # 前端脚本（dev/build/preview 等）
├─ .env.example               # 环境变量示例（复制为 .env）
├─ config.toml(.template)     # 可选：AI/模型配置模板
├─ config/                    # Python 配置
│  └─ app_config.py           # 读取环境变量与默认设置
├─ src/                       # Python 源码（api/models/utils）
│  ├─ api/
│  ├─ models/
│  └─ utils/
├─ src/                       # React 前端源码（ts/tsx）
│  ├─ components/
│  ├─ pages/
│  ├─ types/
│  └─ utils/
├─ dist/                      # 前端构建产物（Vite 生成）
└─ data/                      # 运行数据（日志/会话/项目）
	├─ logs/
	├─ sessions/
	└─ projects/
```

说明：`data/` 已在 `.gitignore` 中忽略，避免将本地数据推到仓库。

## 环境准备

- Windows 10/11（PowerShell 5.1 或以上）
- Python 3.11+
- Node.js 18+（建议 LTS）

## 安装依赖

```powershell
# Python 依赖（建议在虚拟环境中执行）
python -m pip install -r requirements.txt

# Node 依赖（使用 npm；如用 pnpm/yarn 请替换）
npm install
```

## 配置 API（两种方式）

推荐使用环境变量（.env），也支持 config.toml。

### 方式 A：.env（推荐）

```powershell
Copy-Item .env.example .env -Force
```

编辑 `.env`，至少填写一种服务的密钥：

```
# OpenAI（推荐）
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com

# Anthropic（可选）
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
ANTHROPIC_API_BASE=https://api.anthropic.com

# DeepSeek / Qwen（可选）
DEEPSEEK_API_KEY=...
QWEN_API_KEY=...   # 或 DASHSCOPE_API_KEY=...
```

后端会在运行时从环境变量读取（见 `config/app_config.py`）。

### 方式 B：config.toml（可选）

```powershell
Copy-Item config.example.toml config.toml -Force
# 或
Copy-Item config.toml.template config.toml -Force
```

示例：

```toml
[ai]
openai_api_key   = "sk-..."
openai_base_url  = "https://api.openai.com/v1"
claude_api_key   = "..."
deepseek_api_key = "..."
qwen_api_key     = "..."

[models]
default_chat_model      = "gpt-3.5-turbo"
default_embedding_model = "text-embedding-3-small"
clarifier_model   = "gpt-4o-mini"
innovator_model   = "claude-3-haiku-20240307"
critic_model      = "gpt-3.5-turbo"
synthesizer_model = "deepseek-chat"
verifier_model    = "gpt-4o-mini"
summarizer_model  = "gpt-3.5-turbo"

[system]
max_tokens     = 4000
temperature    = 0.7
max_iterations = 10
```

## 启动与构建

开发模式（交互式脚本，推荐）：

```powershell
python start.py
```

手动分开启动（便于调试）：

```powershell
# 终端 1：Vite 开发服务器
npm run dev

# 终端 2：Python 后端（Eel）
python main.py
```

生产模式（本地运行）：

```powershell
# 自动构建并启动
python start_production.py

# 或手动两步：
npm run build
python main.py
```

package.json 常用脚本：`dev`（前端开发）、`build`（构建 dist/）、`start`（python start.py）、`prod`（python start_production.py）。

## 常见问题（Windows/PowerShell）

1) `npm run build` 失败（Exit Code: 1）
- 确认 Node ≥ 18：`node -v`
- 重新安装依赖：`npm install`
- 使用 `npx tsc --noEmit` 定位类型报错

2) `python start_production.py` 失败
- 未检测到包管理器时请安装 Node.js 并加入 PATH
- 端口占用（默认 8000），可设置：`$env:EEL_PORT=8010`
- 确保 `requirements.txt` 安装成功

3) 纯后端模式（无前端界面）

```powershell
$env:IDEAARCHITECT_MODE="python_only"; python main.py
```

## 日志与数据

- 日志：`data/logs/ideaarchitect.log`
- 项目：`data/projects/`
- 会话：`data/sessions/`

上述目录会在首次运行时自动创建，均被 `.gitignore` 忽略。

## 许可证

MIT（见 `LICENSE`）。

## API 概览（Eel 暴露接口）

后端通过 Eel 暴露一组简化 API，供前端 `src/utils/eel-api.ts` 调用：

- 项目 Project
	- `api_create_project(project_data)`
	- `api_load_project(project_id)`
	- `api_save_project(project_data)`
	- `api_list_projects()`
	- `api_delete_project(project_id)`
- 工作流 Workflow
	- `api_start_workflow(project_id, initial_idea, workflow_mode)`
	- `api_get_workflow_status(session_id)`
	- `api_pause_workflow(session_id)`
	- `api_resume_workflow(session_id)`
	- `api_stop_workflow(session_id)`
- 智能体 Agent（示例实现）
	- `api_list_agents()`
	- `api_create_agent(name, role, model, description)`
	- `api_get_agent_status(agent_id)`
	- `api_configure_agent(agent_id, config)`

如需新增接口：在 `src/api/` 添加函数，并在 `main.py` 使用 `@eel.expose` 暴露，然后前端通过 `eel-api.ts` 调用。

## 开发说明（前后端衔接）

前端已通过 `eel-api.ts` 适配到 Python/Eel：

1. 将原 `@tauri-apps/api/core` 的 `invoke` 调用替换为 `eel-api.ts` 中的 `invoke`。
2. 使用事件总线推送工作流进度（参见 `src/utils/event_bus.py` 与前端事件监听）。
3. UI 组件与路由（React + Vite）保持不变，仅替换数据源。

## 故障排除（FAQ）

1) Eel 脚本加载失败或端口占用
- 确认 Python 后端已启动；默认端口 8000，可通过环境变量调整：`$env:EEL_PORT=8010`

2) 前端依赖或构建失败
- 重新安装依赖：`npm install`
- 确认 Node 版本 ≥ 18：`node -v`
- 使用 `npx tsc --noEmit` 定位类型错误

3) Python 依赖缺失
- 执行 `python -m pip install -r requirements.txt`
- 确认 Python 版本为 3.11+

## 日志与数据位置

- 日志：`data/logs/ideaarchitect.log`
- 项目：`data/projects/`
- 会话：`data/sessions/`

首次运行会自动创建上述目录；这些目录均已在 `.gitignore` 中忽略。

—— 若你需要英文版 README、徽章/截图或更细的功能清单，请告诉我，我可以直接补充。
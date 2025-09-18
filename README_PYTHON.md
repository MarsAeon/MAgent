# IdeaArchitect - 多智能体想法完成引擎

基于Eel框架的Python桌面应用程序，使用现有的React前端界面。

## 快速开始

### 1. 环境要求

- Python 3.11+
- Node.js 16+
- npm 或 yarn

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Node.js依赖
npm install
```

### 3. 配置环境

复制环境配置文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，添加您的AI模型API密钥：
```
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 4. 启动应用

使用启动脚本（推荐）：
```bash
python start.py
```

或者手动启动：

**开发模式：**
```bash
# 启动前端开发服务器
npm run dev

# 在另一个终端启动Python后端
python main.py
```

**生产模式：**
```bash
# 构建前端
npm run build

# 启动Python应用
python main.py
```

## 项目结构

```
MAgent/
├── main.py                 # Python应用入口
├── start.py                # 启动脚本
├── requirements.txt        # Python依赖
├── config/                 # 配置文件
│   └── app_config.py
├── src/                    # Python源码
│   ├── api/               # API接口层
│   ├── models/            # 数据模型
│   └── utils/             # 工具模块
├── src/                    # React前端源码（现有）
│   ├── components/        # React组件
│   ├── pages/             # 页面组件
│   ├── types/             # TypeScript类型
│   └── utils/             # 前端工具
├── index.html              # 主页面
├── package.json            # Node.js配置
└── vite.config.ts          # Vite配置
```

## 功能特性

- ✅ 项目管理（创建、加载、保存、删除）
- ✅ 多智能体工作流编排
- ✅ 实时进度显示和状态同步
- ✅ 错误处理和日志记录
- ✅ 现有React UI界面保留
- ✅ Eel与Python后端集成

## API接口

### 项目管理
- `api_create_project(name, description, initial_idea)`
- `api_load_project(project_id)`
- `api_save_project(project_data)`
- `api_list_projects()`
- `api_delete_project(project_id)`

### 工作流管理
- `api_start_workflow(project_id, initial_idea, workflow_mode)`
- `api_get_workflow_status(session_id)`
- `api_pause_workflow(session_id)`
- `api_resume_workflow(session_id)`
- `api_stop_workflow(session_id)`

### 智能体管理
- `api_list_agents()`
- `api_create_agent(name, role, model, description)`
- `api_get_agent_status(agent_id)`
- `api_configure_agent(agent_id, config)`

## 开发说明

### 前端集成

现有的React前端已通过Eel适配层与Python后端集成：

1. **API调用替换**：将`@tauri-apps/api/core`的`invoke`替换为`src/utils/eel-api.ts`中的`invoke`
2. **事件系统**：通过Eel的事件总线实现实时通信
3. **UI保留**：完全保留现有的用户界面和交互逻辑

### 添加新功能

1. 在`src/api/`中添加新的API函数
2. 在`main.py`中使用`@eel.expose`暴露函数
3. 在前端通过`eel-api.ts`调用新函数

## 故障排除

### 常见问题

1. **Eel脚本加载失败**
   - 确保Python应用已启动
   - 检查端口8000是否被占用

2. **前端构建失败**
   - 运行`npm install`重新安装依赖
   - 检查Node.js版本是否符合要求

3. **Python依赖缺失**
   - 运行`pip install -r requirements.txt`
   - 确保Python版本为3.11+

### 日志查看

应用日志保存在`data/logs/`目录：
- `ideaarchitect.log` - 应用日志
- `error.log` - 错误日志

## 许可证

MIT License

## 模型与API密钥配置

要启用基于大模型的“智能问答澄清”能力，请在系统环境变量或 `.env` 中配置以下任意一组：

```
# OpenAI（推荐）
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_API_BASE=https://api.openai.com

# Anthropic（可选，作为备选）
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620
ANTHROPIC_API_BASE=https://api.anthropic.com
```

未配置任何密钥时，系统会回退到启发式的固定问题列表，依然可用但智能度较低。

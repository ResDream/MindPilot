# <center>MindPilot 🚀

<div align="center">

**跨平台的桌面智能体助手 · Cross-platform Desktop Agent**

**Language**: [English](README.md) | [中文](README-zh.md)

</div>

![MindPilot](docs/images/home.png)

## 简介

[**MindPilot**](https://github.com/ResDream/MindPilot) 是一个跨平台的桌面 Agent 助手。用自然语言下达任务，它会自动拆解、规划、调用工具并总结结果——每一步都在任务时间线上清晰可见。

模型层面同时支持**在线模型**（任意 OpenAI 兼容接口）和基于 [**MindSpore**](https://github.com/mindspore-ai/mindspore) / [**MindNLP**](https://github.com/mindspore-lab/mindnlp) 的**本地离线模型**，可在 CPU、GPU 及昇腾设备上运行。

## 功能特性

- 🧠 **任务驱动的 Agent**——自动拆解与规划任务，思考步骤和工具调用以时间线形式可视化，不再是黑盒。
- 🛠️ **自定义智能体**——为不同场景创建专属 Agent，可配置人设、温度、工具与知识库。
- 🌐 **内置工具**——联网搜索（Bing）、arxiv 论文检索、Wolfram、计算器、天气、Shell、本地知识库检索。
- 📚 **RAG 知识库**——支持 PDF / Word / PPT / CSV / 图片（OCR）解析，中文优化的文本切分，FAISS / Milvus / Elasticsearch 向量库 + BM25 混合检索。
- 🔌 **OpenAI 兼容**——`base_url` 指向任意兼容端点即可（OpenAI、DeepSeek、通义、本地 vLLM 等）。
- 🔒 **离线模式**——通过 MindNLP 在自有算力服务器上本地运行 Qwen2.5-72B-Instruct 等开源模型，无需联网。
- 🖥️ **跨平台**——Windows、macOS、Linux。

## 架构

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│  前端 (Electron)         │  HTTP  │  后端 (FastAPI)              │
│  Vue 3 + TypeScript     │ ─────▶ │  LangChain Agent Executor    │
│  任务时间线 UI           │  SSE   │  工具 · RAG · SQLite         │
└─────────────────────────┘        └──────────────┬───────────────┘
                                                  │
                          ┌───────────────────────┼──────────────────┐
                          ▼                       ▼                  ▼
                    OpenAI 兼容 API        MindSpore / MindNLP    向量数据库
                  (GPT, DeepSeek, ...)     （本地离线模型）        FAISS/Milvus/ES
```

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/ResDream/MindPilot.git
cd MindPilot
```

### 2. 启动后端

```bash
pip install -r requirements.txt
cd src/mindpilot
python main.py   # 服务地址 http://127.0.0.1:7861
```

### 3. 启动前端

```bash
cd Frontend
yarn
yarn dev
```

打包各平台安装包：

```bash
yarn build:win    # Windows
yarn build:mac    # macOS
yarn build:linux  # Linux
```

### 4. 配置

- **模型**：在侧边栏打开「模型配置」，新增 OpenAI 兼容配置（名称 / base_url / api_key / 模型名），或选择 `Local` 配置使用本地离线推理。
- **工具密钥**：统一从环境变量读取，仓库中不保存任何密钥：

```bash
# Windows (PowerShell)
$env:BING_SEARCH_KEY="你的-bing-key"
$env:WEATHER_API_KEY="你的-天气-key"
$env:WOLFRAM_APPID="你的-wolfram-appid"

# macOS / Linux
export BING_SEARCH_KEY="你的-bing-key"
export WEATHER_API_KEY="你的-天气-key"
export WOLFRAM_APPID="你的-wolfram-appid"
```

### 5. 开始任务

点击「创建智能体」，绑定工具与知识库，然后输入任务。执行过程中的每个思考步骤和工具调用都会实时呈现在时间线上。

## 技术栈

| 层级 | 技术                                                         |
| ---- | ------------------------------------------------------------ |
| 前端 | Electron · Vue 3 · TypeScript · Element Plus · Pinia         |
| 后端 | FastAPI · LangChain · SQLAlchemy · SSE 流式输出              |
| 模型 | OpenAI 兼容 API · MindSpore + MindNLP（本地）                |
| 检索 | FAISS / Milvus / Elasticsearch · BM25 混合检索 · RapidOCR    |

## 路线图

- [ ] 时间线逐 token 流式输出
- [ ] 多智能体协作
- [ ] 自定义工具插件市场
- [ ] 昇腾 NPU 优化构建

## 联系我们

如有问题或建议：[2802427218@qq.com](mailto:2802427218@qq.com)

## 许可证

[Apache License 2.0](LICENSE)

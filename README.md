# <center>MindPilot 🚀

<div align="center">

**跨平台的桌面智能体助手 · Cross-platform Desktop Agent**

**Language**: [English](README.md) | [中文](README-zh.md)

</div>

![MindPilot](docs/images/home.png)

## Introduction

[**MindPilot**](https://github.com/ResDream/MindPilot) is a cross-platform desktop Agent assistant. Give it a task in natural language, and it will decompose, plan, call tools, and summarize the result — with every step visible in a clean task timeline.

It supports both **online models** (any OpenAI-compatible API) and **local offline models** powered by [**MindSpore**](https://github.com/mindspore-ai/mindspore) and [**MindNLP**](https://github.com/mindspore-lab/mindnlp), running on CPU, GPU, or Ascend devices.

## Features

- 🧠 **Task-driven Agent** — tasks are decomposed and planned automatically; thinking steps and tool calls are visualized as a timeline instead of a black box.
- 🛠️ **Custom Agents** — create agents with their own persona, temperature, tools, and knowledge bases for different scenarios.
- 🌐 **Built-in Tools** — web search (Bing), arXiv, Wolfram, calculator, weather, shell, and local knowledge base retrieval.
- 📚 **RAG Knowledge Base** — PDF / Word / PPT / CSV / image (OCR) parsing, Chinese-optimized text splitting, FAISS / Milvus / Elasticsearch vector stores with hybrid BM25 retrieval.
- 🔌 **OpenAI-compatible** — point `base_url` at any compatible endpoint (OpenAI, DeepSeek, Qwen, local vLLM, etc.).
- 🔒 **Offline Mode** — run open-source models such as Qwen2.5-72B-Instruct locally through MindNLP on your own GPU servers, no network required.
- 🖥️ **Cross-platform** — Windows, macOS, and Linux.

## Architecture

```
┌─────────────────────────┐        ┌──────────────────────────────┐
│  Frontend (Electron)    │  HTTP  │  Backend (FastAPI)           │
│  Vue 3 + TypeScript     │ ─────▶ │  LangChain Agent Executor    │
│  Task timeline UI       │  SSE   │  Tools · RAG · SQLite        │
└─────────────────────────┘        └──────────────┬───────────────┘
                                                  │
                          ┌───────────────────────┼──────────────────┐
                          ▼                       ▼                  ▼
                  OpenAI-compatible API    MindSpore / MindNLP   Vector Stores
                  (GPT, DeepSeek, ...)     (local offline LLM)   FAISS/Milvus/ES
```

## Quick Start

### 1. Clone

```bash
git clone https://github.com/ResDream/MindPilot.git
cd MindPilot
```

### 2. Backend

```bash
pip install -r requirements.txt
cd src/mindpilot
python main.py   # serves on http://127.0.0.1:7861
```

### 3. Frontend

```bash
cd Frontend
yarn
yarn dev
```

To build installers:

```bash
yarn build:win    # Windows
yarn build:mac    # macOS
yarn build:linux  # Linux
```

### 4. Configure

- **Model**: open 「模型配置」 in the sidebar, add an OpenAI-compatible config (name / base_url / api_key / model), or pick a `Local` config for offline inference.
- **Tools**: API keys are read from environment variables — no keys are stored in the repo:

```bash
# Windows (PowerShell)
$env:BING_SEARCH_KEY="your-bing-key"
$env:WEATHER_API_KEY="your-weather-key"
$env:WOLFRAM_APPID="your-wolfram-appid"

# macOS / Linux
export BING_SEARCH_KEY="your-bing-key"
export WEATHER_API_KEY="your-weather-key"
export WOLFRAM_APPID="your-wolfram-appid"
```

### 5. Run a task

Create an agent (「创建智能体」), attach tools and a knowledge base, then type your task. MindPilot shows each thinking step and tool call in the timeline as it works.

## Tech Stack

| Layer     | Stack                                                        |
| --------- | ------------------------------------------------------------ |
| Frontend  | Electron · Vue 3 · TypeScript · Element Plus · Pinia         |
| Backend   | FastAPI · LangChain · SQLAlchemy · SSE streaming             |
| LLM       | OpenAI-compatible API · MindSpore + MindNLP (local)          |
| Retrieval | FAISS / Milvus / Elasticsearch · BM25 hybrid · RapidOCR      |

## Roadmap

- [ ] Streaming token-by-token output in the timeline
- [ ] Multi-agent collaboration
- [ ] Plugin marketplace for custom tools
- [ ] Ascend NPU optimized builds

## Contact

Questions or suggestions: [2802427218@qq.com](mailto:2802427218@qq.com)

## License

[Apache License 2.0](LICENSE)

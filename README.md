# <center>MindPilot 🚀
<div align="center">

**Language**: [English](README.md) | [中文](README-zh.md)

</div>

## Introduction

[**MindPilot**](https://github.com/ResDream/MindPilot) is a cross-platform multifunctional intelligent desktop Agent assistant designed to provide users with convenient and efficient smart solutions. It leverages [**MindSpore**](https://github.com/mindspore-ai/mindspore) and [**MindNLP**](https://github.com/mindspore-lab/mindnlp) to integrate advanced large language models as its core decision-making engine. MindPilot can accurately decompose, plan, execute, reflect on, and summarize user tasks, ensuring efficient task completion. ✨

## Key Features

- **Cross-Platform Support** 🌍: Compatible with major operating systems including Windows, macOS, and Linux.
- **Customizable Agents** 🛠️: Users can tailor different agent identities based on their needs, allowing for personalized intelligent services to handle diverse task scenarios.
- **Efficient Execution** ⚡: Advanced algorithms, powered by MindSpore and MindNLP, ensure efficient task completion.
- **Knowledge Base Support** 📚: Integrates a knowledge base to provide contextual information and enhance decision-making capabilities.
- **Hardware Compatibility** 💻: Supports CPU, GPU, and Ascend devices.

## Installation
- Clone
   ```bash
    git clone https://github.com/ResDream/MindPilot.git
   ```
- Frontend 
   ```bash
  # Installation
   cd Frontend
   yarn
  
  # Build for Specific Platforms:
   # For windows
    $ yarn build:win
    
    # For macOS
    $ yarn build:mac
    
    # For Linux
    $ yarn build:linux
   ```
  
- Backend 
    ```bash
    # Install dependencies
    pip install -r requirements.txt
    ```

## Usage Guide

1. **Start MindPilot**:
   ```bash
   # Frontend
   cd Frontend
   yarn dev
   
   # Backend
   cd src/mindpilot
   python main.py
   ```

2. **Search Config**:
    - Open the file src/mindpilot/app/configs/tool_config.py. 
Fill in the bing search API in the following code: 
   ```python
    "search_internet": { 
            "use": False, 
            "search_engine_name": "bing", 
            "search_engine_config": { 
                "bing": { 
                    "result_len": 3, 
                    "bing_search_url": "https://api.bing.microsoft.com/v7.0/search", 
                    "bing_key": "", 
                }, 
            }, 
    ```

3. **Create and Configure Agents** 🛠️:
   - Select "Create Agent" within the app and follow the prompts to complete the setup.

4. **Start Tasks** 📝:
   - Input your task requirements, and MindPilot will automatically decompose and plan them.


## Contact Us 📧

For questions or suggestions, please contact [2802427218@qq.com](mailto:your-email@example.com).

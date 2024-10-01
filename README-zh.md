# <center>MindPilot 🚀
<div align="center">

**Language**: [English](README.md) | [中文](README-zh.md)

</div>

## 简介

[**MindPilot**](https://github.com/ResDream/MindPilot) 是一个跨平台的多功能智能桌面代理助手，旨在为用户提供便捷高效的智能解决方案。它利用 [**MindSpore**](https://github.com/mindspore-ai/mindspore) 和 [**MindNLP**](https://github.com/mindspore-lab/mindnlp)，将先进的大型语言模型作为核心决策引擎。MindPilot 能够准确地分解、规划、执行、反思和总结用户任务，确保任务高效完成。✨

## 主要功能

- **跨平台支持** 🌍: 兼容包括 Windows、macOS 和 Linux 在内的主流操作系统。
- **可定制代理** 🛠️: 用户可以根据需求定制不同的代理身份，提供个性化的智能服务，处理多样化的任务场景。
- **高效执行** ⚡: 由 MindSpore 和 MindNLP 提供支持的高级算法，确保任务高效完成。
- **知识库支持** 📚: 集成知识库，为决策提供上下文信息，增强决策能力。
- **硬件兼容性** 💻: 支持 CPU、GPU 和 Ascend 设备。

## 安装
- 克隆
   ```bash
    git clone https://github.com/ResDream/MindPilot.git
   ```
- 前端 
   ```bash
  # 安装依赖
   cd Frontend
   yarn
  
  # 为指定平台构建:
   # Windows 平台
    $ yarn build:win
    
    # macOS 平台
    $ yarn build:mac
    
    # Linux 平台
    $ yarn build:linux
   ```
  
- 后端 
    ```bash
    # 安装依赖
    pip install -r requirements.txt
    ```

## 使用指南

1. **启动 MindPilot**:
   ```bash
   # 前端
   cd Frontend
   yarn dev
   
   # 后端
   cd src/mindpilot
   python main.py
   ```

2. **配置搜索功能**:
    - 打开文件 `src/mindpilot/app/configs/tool_config.py`。在如下代码中填入 Bing 搜索 API:
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

3. **创建并配置代理** 🛠️:
   - 在应用内选择“创建代理”，并按照提示完成设置。

4. **启动任务** 📝:
   - 输入你的任务需求，MindPilot 将自动分解并规划任务。

## 联系我们 📧

如有任何问题或建议，请联系 [2802427218@qq.com](mailto:your-email@example.com)。

---

**让我们一起打造更智能的助手！** 🌟
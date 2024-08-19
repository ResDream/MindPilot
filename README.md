# MindPilot
MindPilot是一个跨平台的多功能智能Agent桌面助手，旨在为用户提供便捷、高效的智能解决方案。通过集成先进的大语言模型作为核心决策引擎，MindPilot能够对用户的任务进行精准分解、规划、执行、反思和总结，确保任务的高效完成。同时提供了高度自定义化的Agent，用户可以根据需求自定义不同身份的Agent，以应对多样化的任务场景，实现个性化的智能服务。在MindSpore的支持下，MindPilot支持Windows、macOS和Linux等主流操作系统，并兼容多种在线模型API和本地模型，能流畅运行在CPU，GPU，Ascend设备上。

# QuickStart

## 前端

## Recommended IDE Setup

- [VSCode](https://code.visualstudio.com/) + [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint) + [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) + [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) + [TypeScript Vue Plugin (Volar)](https://marketplace.visualstudio.com/items?itemName=Vue.vscode-typescript-vue-plugin)

## Project Setup

### 安装

```bash
$ yarn
```

### 启动

```bash
$ yarn dev
```

### Build

```bash
# For windows
$ yarn build:win

# For macOS
$ yarn build:mac

# For Linux
$ yarn build:linux
```

## 后端

### 安装

```bash
pip install -r requirements.txt
```

### 启动

```bash
python src\mindpilot\main.py 
```
>注意：在使用星火大模型时，需要运行下面代码打开转发服务器
> ```bash
> python -m sparkai.spark_proxy.main 
> ```
> 
> base_url为http://localhost:8008/v1
> 
> api_key需要设置为 <SPARKAI_API_KEY>&<SPARKAI_API_SECRET>&<SPARKAI_APP_ID>
> 
> model名需要设置为4.0Ultra
> 
> 由于我们使用的Spark 4.0Ultra能力强大，自带Agent能力，因此不建议启动本地Agent流程
> 
> 当使用Spark 4.0Ultra时，由于spark_ai_python不支持Spark 4.0Ultra，需要替换库文件spark_api的model_map为：
> 
>{
>'generalv3.5': 'wss://spark-api.xf-yun.com/v3.5/chat',
>'iflycode.ge': 'wss://spark-api.xf-yun.com/v3.2/chat',
>'generalv3.5tipre': 'wss://spark-openapi.cn-huabei-1.xf-yun.com/v3.5/chat',
>'4.0Ultra':'wss://spark-api.xf-yun.com/v4.0/chat'
}
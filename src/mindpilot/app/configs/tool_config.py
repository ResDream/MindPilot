TOOL_CONFIG = {
        # "search_local_knowledgebase": {
        #     "use": False,
        #     "top_k": 3,
        #     "score_threshold": 1.0,
        #     "conclude_prompt": {
        #         "with_result": '<指令>根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 "根据已知信息无法回答该问题"，'
        #                        "不允许在答案中添加编造成分，答案请使用中文。 </指令>\n"
        #                        "<已知信息>{{ context }}</已知信息>\n"
        #                        "<问题>{{ question }}</问题>\n",
        #         "without_result": "请你根据我的提问回答我的问题:\n"
        #                           "{{ question }}\n"
        #                           "请注意，你必须在回答结束后强调，你的回答是根据你的经验回答而不是参考资料回答的。\n",
        #     },
        # },
        "search_internet": {
            "use": False,
            "search_engine_name": "bing",
            "search_engine_config": {
                "bing": {
                    "result_len": 3,
                    "bing_search_url": "https://api.bing.microsoft.com/v7.0/search",
                    "bing_key": "0f42b09dce16474a81c01562ded071dc",
                },
                "metaphor": {
                    "result_len": 3,
                    "metaphor_api_key": "",
                    "split_result": False,
                    "chunk_size": 500,
                    "chunk_overlap": 0,
                },
                "duckduckgo": {"result_len": 3},
            },
            "top_k": 10,
            "verbose": "Origin",
            "conclude_prompt": "<指令>这是搜索到的互联网信息，请你根据这些信息进行提取并有调理，简洁的回答问题。如果无法从中得到答案，请说 “无法搜索到能回答问题的内容”。 "
                               "</指令>\n<已知信息>{{ context }}</已知信息>\n"
                               "<问题>\n"
                               "{{ question }}\n"
                               "</问题>\n",
        },
        "arxiv": {
            "use": False,
        },
        "shell": {
            "use": False,
        },
        "weather_check": {
            "use": False,
            "api_key": "SE7CGiRD5dvls08Ub",
        },
        # "search_youtube": {
        #     "use": False,
        # },
        "wolfram": {
            "use": False,
            "appid": "PWKVLW-6ETR93QX6Q",
        },
        "calculate": {
            "use": False,
        },
        # "vqa_processor": {
        #     "use": False,
        #     "model_path": "your model path",
        #     "tokenizer_path": "your tokenizer path",
        #     "device": "cuda:1",
        # },
        # "aqa_processor": {
        #     "use": False,
        #     "model_path": "your model path",
        #     "tokenizer_path": "yout tokenizer path",
        #     "device": "cuda:2",
        # },
        # "text2images": {
        #     "use": False,
        # },
    }
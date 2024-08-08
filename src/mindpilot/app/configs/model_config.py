MODEL_CONFIG = {
            # "preprocess_model": {
            #     "glm-4": {
            #         "temperature": 0.05,
            #         "max_tokens": 4096,
            #         "history_len": 100,
            #         "prompt_name": "default",
            #         "callbacks": True,
            #     },
            # },
            "platform": "OpenAI",
            "is_openai": True,
            "base_url": "https://api.chatanywhere.tech/v1/",
            "api_key": "sk-cERDW9Fr2ujq8D2qYck9cpc9MtPytN26466bunfYXZVZWV7Y",
            "llm_model": {
                "gpt-4o-mini": {
                    "temperature": 0.8,
                    "max_tokens": 8192,
                    "history_len": 10,
                    "prompt_name": "default",
                    "callbacks": True,
                },
            },
            # "action_model": {
            #     "glm-4": {
            #         "temperature": 0.1,
            #         "max_tokens": 4096,
            #         "prompt_name": "ChatGLM3",
            #         "callbacks": True,
            #     },
            # },
            # "postprocess_model": {
            #     "glm-4": {
            #         "temperature": 0.1,
            #         "max_tokens": 4096,
            #         "prompt_name": "default",
            #         "callbacks": True,
            #     }
            # }
    }
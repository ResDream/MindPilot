MODEL_CONFIG = {
            "preprocess_model": {
                "glm-4": {
                    "temperature": 0.05,
                    "max_tokens": 4096,
                    "history_len": 100,
                    "prompt_name": "default",
                    "callbacks": True,
                },
            },
            "llm_model": {
                # "glm-4": {
                #     "temperature": 0.8,
                #     "max_tokens": 4096,
                #     "history_len": 10,
                #     "prompt_name": "default",
                #     "callbacks": True,
                # },
                "gpt-4o-mini": {
                    "temperature": 0.8,
                    "max_tokens": 8192,
                    "history_len": 10,
                    "prompt_name": "default",
                    "callbacks": True,
                },
            },
            "action_model": {
                "glm-4": {
                    "temperature": 0.1,
                    "max_tokens": 4096,
                    "prompt_name": "ChatGLM3",
                    "callbacks": True,
                },
            },
            "postprocess_model": {
                "glm-4": {
                    "temperature": 0.1,
                    "max_tokens": 4096,
                    "prompt_name": "default",
                    "callbacks": True,
                }
            }
    }
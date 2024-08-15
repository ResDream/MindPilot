import sqlite3


def get_config_from_id(config_id: int):
    conn = sqlite3.connect('mindpilot.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM model_configs WHERE id = ?', (config_id,))
    config = cursor.fetchone()
    conn.close()

    if not config:
        return None

    config_dict = {
        "config_id": config[0],
        "config_name": config[1],
        "platform": config[2],
        "base_url": config[3],
        "api_key": config[4],
        "llm_model": {
            config[5]: {
                "temperature": config[8],
                "max_tokens": config[7],
                "callbacks": config[6],
            }
        }
    }

    return config_dict

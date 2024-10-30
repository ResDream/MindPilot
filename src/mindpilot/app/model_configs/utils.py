import sqlite3

from src.mindpilot.app.utils.system_utils import get_resource_path


def get_config_from_id(config_id: int):
    db_path = get_resource_path('mindpilot.db')
    conn = sqlite3.connect(db_path)
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

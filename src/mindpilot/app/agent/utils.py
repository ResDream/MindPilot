import sqlite3


def get_agent_from_id(agent_id:int):
    conn = sqlite3.connect('agents.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM agents WHERE id = ?', (agent_id,))
    agent = cursor.fetchone()
    conn.close()

    if not agent:
        return None

    agent_dict = {
        "id": agent[0],
        "agent_name": agent[1],
        "agent_abstract": agent[2],
        "agent_info": agent[3],
        "temperature": agent[4],
        "max_tokens": agent[5],
        "tool_config": agent[6].split(',') if agent[6] else [],
        "kb_name": agent[7].split(',') if agent[7] else [],
        "avatar": agent[8]
    }

    return agent_dict
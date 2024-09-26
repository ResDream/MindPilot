export interface Agent {
  agent_id?: number;
  agent_name: string;
  agent_abstract: string;
  agent_info: string;
  temperature: number;
  max_tokens: number;
  tool_config: string[];
  kb_name?: string[];
  avatar?: string;
  agent_enable?: boolean;
}

export interface backendChat {
  content: string;
  role: string;
}

export interface HistoryItems {
  id: string;
  text: string;
  timestamp: Date;
  summarized: boolean;
}

export interface configManagementFormInterface {
  config_name: string;
  platform: string;
  base_url: string;
  api_key: string;
  llm_model: {
    model: string
    callbacks: boolean
    max_tokens: number
    temperature: number
  };
}

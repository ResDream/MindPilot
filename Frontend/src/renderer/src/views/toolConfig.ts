import { ref } from 'vue'
import axios from 'axios'

export interface Tool {
  value: string
  label: string
}

export const useToolConfig = () => {
  const availableTools = ref<Tool[]>([])
  const selectedTools = ref<string[]>([])



  const fetchAvailableTools = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:7861/api/tools/available_tools')
      if (response.data && response.data.tools) {
        availableTools.value = response.data.tools.map((tool: string) => ({
          value: tool,
          label: tool
        }))
      }
    } catch (error) {
      console.error('Failed to fetch available tools:', error)
    }
  }

  return {
    availableTools,
    selectedTools,
    fetchAvailableTools
  }
}

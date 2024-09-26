import { defineStore } from 'pinia'
import { ref } from 'vue'
import { Conversation } from '../views/conversationApi'

export const useModelConfigStore = defineStore('modelConfigStore', () => {
  const config_id_cache = ref('')

  const setConfigId = (configId: string) => {
    config_id_cache.value = configId
  }

  const getConfigId = () => {
    return config_id_cache.value
  }

  return { config_id_cache, setConfigId, getConfigId }
})
export const useConversationStore = defineStore('conversationStore', () => {
  const currentConversation = ref<Conversation | null>(null)

  const setCurrentConversation = (conversation: Conversation | null) => {
    currentConversation.value = conversation
  }
  const getCurrentConversation = () => {
    return currentConversation.value
  }
  return { currentConversation, setCurrentConversation, getCurrentConversation }
})

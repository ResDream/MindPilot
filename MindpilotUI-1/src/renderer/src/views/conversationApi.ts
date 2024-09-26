import { reactive, ref, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { clearMessageElement, extractFirstJSON } from './utils'
import { Signals } from 'deep-chat/dist/types/handler'
import type { DeepChat } from 'deep-chat'
import { generateAssistantWithRandomID } from '../utils/tools'
import { Agent } from './type'
import { useConversationStore } from '../store/store'

const API_BASE_URL = 'http://127.0.0.1:7861/api'

export interface Conversation {
  conversation_id: string
  title: string
  created_at: string
  updated_at: string
  is_summarized: boolean
  agent_id: number
}

export interface Message {
  message_id: number
  agent_status: number
  role: string
  text: string
  files?: Array<{ name: string; src: string; type: string }>
  timestamp: string
}

export interface SendMessage {
  role: string
  agent_id: number
  config_id: number
  text: string
  files?: string[]
  tool_config: string[]
  temperature: number
  max_tokens: number
}

export interface ChatHistory {
  content: string
  role: string
}

export interface DebugConversationConfig {
  config_id: number | null
  agent_config: Agent // 假设 Agent 类型已在其他地方定义
  history: ChatHistory[]
}

export function useConversation() {
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const error = ref<string | null>(null)
  const localConversationConfig = ref<SendMessage>({
    role: 'user',
    agent_id: NaN,
    config_id: NaN,
    text: '',
    tool_config: [],
    temperature: 1,
    max_tokens: 4096
  })

  watch(
    localConversationConfig,
    async (newValue) => {
      console.log('localConversationConfig:', newValue)
    },
    { deep: true }
  )

  watch(currentConversation, async (newValue) => {
    useConversationStore().setCurrentConversation(newValue)
  })

  const createConversation = async (agent_id: number): Promise<Conversation> => {
    try {
      const response = await axios.post(`${API_BASE_URL}/conversation`, agent_id)
      const newConversation: Conversation = response.data.data
      currentConversation.value = newConversation
      conversations.value.push(newConversation)
      error.value = null
      return newConversation
    } catch (err) {
      console.error('Failed to create conversation:', err)
      error.value = 'Failed to create conversation'
      throw err // Re-throw the error so it can be caught by the caller
    }
  }

  const getConversations = async (): Promise<Conversation[]> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversations`)
      const fetchedConversations = response.data.data
      conversations.value = fetchedConversations
      error.value = null
      return fetchedConversations
    } catch (err) {
      console.error('Failed to get conversations:', err)
      error.value = 'Failed to get conversations'
      return []
    }
  }

  const getConversationDetails = async (conversation_id: string): Promise<void> => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversation/${conversation_id}`)
      currentConversation.value = response.data.data
      messages.value = response.data.data.messages
      error.value = null
    } catch (err) {
      console.error('Failed to get conversation details:', err)
      error.value = 'Failed to get conversation details'
    }
  }
  const switchConversation = async (
    conversation: Conversation,
    chatElementRef: DeepChat
  ): Promise<void> => {
    try {
      await getConversationDetails(conversation.conversation_id)
      currentConversation.value = conversation
      console.log('localConversationConfig.value.agent_id:', localConversationConfig.value.agent_id)
      console.log('conversation.agent_id:', conversation.agent_id)
      localConversationConfig.value.agent_id = conversation.agent_id
      error.value = null

      // Clear the chat interface
      if (chatElementRef) {
        chatElementRef.clearMessages()
        clearMessageElement(chatElementRef)
      }

      console.log(messages.value)
      // 加载消息
      messages.value.forEach((message) => {
        if (chatElementRef) {
          if (message.agent_status === 3) {
            const extractJson = extractFirstJSON(message.text)
            if (extractJson) {
              if (extractJson['action'] === 'Final Answer') {
                chatElementRef.addMessage({
                  text: extractJson['action_input'],
                  role: generateAssistantWithRandomID()
                })
              } else {
                const htmlContent = `<json-collapse label="执行 ${extractJson['action']}" data-json='${JSON.stringify(extractJson)}'></json-collapse>`
                chatElementRef.addMessage({
                  html: htmlContent,
                  role: generateAssistantWithRandomID()
                })
              }
            } else {
              chatElementRef.addMessage({
                text: message.text,
                role: generateAssistantWithRandomID()
              })
            }
          } else if (message.agent_status === 7) {
            const htmlContent = `<message-collapse data-message="${message.text}"></message-collapse>`
            chatElementRef.addMessage({ html: htmlContent, role: generateAssistantWithRandomID() })
          } else {
            chatElementRef.addMessage({ text: message.text, role: message.role })
          }
        }
      })
    } catch (err) {
      console.error('Failed to switch conversation:', err)
      error.value = 'Failed to switch conversation'
    }
  }

  const handleMessage = async (body, signals: Signals, chatElementRef: DeepChat) => {
    console.log('localConversationConfig.value:', localConversationConfig.value)
    console.log('body:', body)
    const url = `${API_BASE_URL}/conversation/${currentConversation.value!.conversation_id}/messages`
    const requestBody: SendMessage = {
      role: 'user',
      agent_id: localConversationConfig.value.agent_id,
      config_id: localConversationConfig.value.config_id,
      text: body.messages[0].text,
      tool_config: localConversationConfig.value.tool_config,
      temperature: localConversationConfig.value.temperature,
      max_tokens: localConversationConfig.value.max_tokens
    }
    console.log('requestBody: ', requestBody)
    try {
      const response = await axios.post(url, requestBody, {
        headers: {
          accept: 'application/json',
          'Content-Type': 'application/json'
        }
      })
      if (response.data.code === 200) {
        console.log('Response:', response)
        const responseMessages = response.data.data
        console.log('responseMessages:', responseMessages)
        for (let i = 0; i < responseMessages.length; i++) {
          if (i !== responseMessages.length - 1 && responseMessages[i].agent_status === 3) {
            const extractJson = extractFirstJSON(responseMessages[i].text)
            if (extractJson) {
              const htmlContent = `<json-collapse label="执行 ${extractJson['action']}" data-json='${JSON.stringify(extractJson)}'></json-collapse>`
              chatElementRef.addMessage({
                html: htmlContent,
                role: generateAssistantWithRandomID()
              })
            } else {
              chatElementRef.addMessage({
                text: responseMessages[i].text,
                role: generateAssistantWithRandomID()
              })
            }
          } else if (responseMessages[i].agent_status === -1) {
            signals.onResponse({
              text: responseMessages[0].text,
              role: generateAssistantWithRandomID()
            })
          } else if (responseMessages[i].agent_status === 7) {
            const htmlContent = `<message-collapse data-message="${responseMessages[i].text}"></message-collapse>`
            chatElementRef.addMessage({ html: htmlContent, role: generateAssistantWithRandomID() })
          } else if (i === responseMessages.length - 1) {
            const extractJson = extractFirstJSON(responseMessages[i].text)
            if (extractJson) {
              const finalAnswer = extractJson['action_input']
              signals.onResponse({ text: finalAnswer, role: generateAssistantWithRandomID() })
            }
          }
        }
        await getConversationDetails(currentConversation.value!.conversation_id)
      } else {
        signals.onResponse({ error: '发送消息时发生错误，请重试' })
      }
    } catch (error) {
      ElMessage.error('发送消息时发生错误，请重试')
      signals.onResponse({ error: '发送消息时发生错误，请重试' })
    }
  }

  const debugConversationConfig: DebugConversationConfig = reactive({
    config_id: null,
    agent_config: {} as Agent,
    history: []
  })

  const handleDebugConversation = async (body, signals: Signals, chatElementRef: DeepChat) => {
    const url = `${API_BASE_URL}/conversation/debug`
    const requestBody = {
      config_id: debugConversationConfig.config_id,
      query: body.messages[0].text,
      history: debugConversationConfig.history,
      agent_config: debugConversationConfig.agent_config
    }
    console.log('requestBody: ', requestBody)
    try {
      const response = await axios.post(url, requestBody, {
        headers: {
          accept: 'application/json',
          'Content-Type': 'application/json'
        }
      })
      if (response.data.code === 200) {
        console.log('Response:', response)
        const responseMessages = response.data.data
        console.log('responseMessages:', responseMessages)
        for (let i = 0; i < responseMessages.length; i++) {
          if (i !== responseMessages.length - 1 && responseMessages[i].agent_status === 3) {
            const extractJson = extractFirstJSON(responseMessages[i].text)
            if (extractJson) {
              console.log('exractJson: ', extractJson)
              const htmlContent = `<json-collapse label="执行 ${extractJson['action']}" data-json='${JSON.stringify(extractJson)}'></json-collapse>`
              chatElementRef.addMessage({
                html: htmlContent,
                role: generateAssistantWithRandomID()
              })
            } else {
              chatElementRef.addMessage({
                text: responseMessages[i].text,
                role: generateAssistantWithRandomID()
              })
            }
          } else if (responseMessages[i].agent_status === -1) {
            signals.onResponse({
              text: responseMessages[0].text,
              role: generateAssistantWithRandomID()
            })
          } else if (responseMessages[i].agent_status === 7) {
            const htmlContent = `<message-collapse data-message="${responseMessages[i].text}"></message-collapse>`
            chatElementRef.addMessage({ html: htmlContent, role: generateAssistantWithRandomID() })
          } else if (i === responseMessages.length - 1) {
            const extractJson = extractFirstJSON(responseMessages[i].text)
            if (extractJson) {
              const finalAnswer = extractJson['action_input']
              signals.onResponse({ text: finalAnswer, role: generateAssistantWithRandomID() })
            }
          }
        }
      } else {
        signals.onResponse({ error: '发送消息时发生错误，请重试' })
      }
    } catch (error) {
      console.log(error)
      ElMessage.error('发送消息时发生错误，请重试')
      signals.onResponse({ error: '发送消息时发生错误，请重试' })
    }
  }

  const deleteConversation = async (conversation_id: string): Promise<void> => {
    try {
      await axios.delete(`${API_BASE_URL}/conversation/${conversation_id}`)
      conversations.value = conversations.value.filter(
        (conv) => conv.conversation_id !== conversation_id
      )
      if (currentConversation.value?.conversation_id === conversation_id) {
        currentConversation.value = null
        messages.value = []
      }
      error.value = null
    } catch (err) {
      console.error('Failed to delete conversation:', err)
      error.value = 'Failed to delete conversation'
    }
  }

  return {
    conversations,
    currentConversation,
    messages,
    error,
    createConversation,
    getConversations,
    debugConversationConfig,
    getConversationDetails,
    handleDebugConversation,
    deleteConversation,
    localConversationConfig,
    switchConversation,
    handleMessage
  }
}

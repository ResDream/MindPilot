<template>
  <div class="common-layout">
    <div class="aside-area">
      <el-card class="box-card">
        <div class="card-header">
          &nbsp;
          <span class="align-middle">MindPilot</span>
        </div>
      </el-card>
      <el-menu :default-active="'2'" class="el-menu-vertical-demo" @select="handleSelect">
        <div v-contextmenu:contextmenu>
          <el-menu-item
            v-for="agent in agents"
            :key="agent.agent_id"
            :index="(agent.agent_id as number).toString()"
            @click="handleOptionClick($event, agent)"
            @contextmenu="handleContextMenu($event, agent)"
          >
            <img
              :src="agent.avatar || uploadIcon"
              alt="Agent Avatar"
              class="thumbnail align-middle"
              style="border-radius: 50%; padding-right: 5px"
            />
            <el-text class="agent-list align-middle" truncated> {{ agent.agent_name }}</el-text>
          </el-menu-item>
        </div>
      </el-menu>
      <el-divider class="menu-divider" content-position="left" border-style="dashed">
        <template #default>
          <span class="history-text">历史记录</span>
        </template>
      </el-divider>

      <el-scrollbar class="el-scrollbar">
        <el-menu :default-active="currentConversation?.conversation_id" class="conversation-menu">
          <div v-contextmenu:conversationMenu>
            <el-menu-item
              v-for="conversation in [...conversations].reverse()"
              :key="conversation.conversation_id"
              :index="conversation.conversation_id"
              @click="handleSwitchConversation(conversation)"
              @contextmenu="handleConversationContextMenu($event, conversation)"
            >
              <el-text class="agent-list align-middle" truncated>{{ conversation.title }}</el-text>
            </el-menu-item>
          </div>
        </el-menu>
      </el-scrollbar>
      <div class="aside-buttons">
        <div>
          <span
            style="margin-right: 20%"
            class="agent-list align-middle small-font"
            @click="toKBConfig"
            >知识库管理</span
          >
        </div>
        <el-divider direction="horizontal" border-style="dashed" />
        <span
          class="agent-list align-middle small-font"
          @click="isShowConfigManagementDialog = true"
        >
          配置管理
        </span>
        <el-divider direction="vertical" border-style="dashed" />
        <span class="agent-list align-middle small-font" @click="toAgentConfig"> 创建智能体 </span>
      </div>
    </div>

    <div class="main-container">
      <div class="header-area">
        <el-menu mode="horizontal" class="horizontal-menu">
          <el-sub-menu>
            <template #title>{{ chatSettings.config_name || '未选择配置' }}</template>
            <el-menu-item
              v-for="config in configs"
              :key="config.config_id"
              :index="config.config_id ?? ''"
              @click="selectModel(config)"
            >
              {{ config.config_name }}
            </el-menu-item>
          </el-sub-menu>
        </el-menu>
        <div class="chat-header">
          <span>{{ headerText }}</span>
        </div>
      </div>
      <div class="main-content">
        <div class="chat-container">
          <div class="chat-controls">
            <el-form label-position="top">
              <el-form-item label="温度">
                <el-slider
                  v-model="localConversationConfig.temperature"
                  :min="0.1"
                  :max="1"
                  :step="0.1"
                />
              </el-form-item>
              <el-form-item label="最大Token">
                <el-input-number
                  v-model="localConversationConfig.max_tokens"
                  :min="1"
                  :max="4096"
                />
              </el-form-item>
              <el-form-item v-if="selectedAgentId !== -1" label="是否启用Agent">
                <el-switch v-model="isAgentEnabled" />
              </el-form-item>
              <el-form-item v-if="selectedAgentId !== -1" label="可选工具">
                <el-select v-model="selectedTools" multiple collapse-tags collapse-tags-tooltip>
                  <el-option
                    v-for="item in availableTools"
                    :key="item.value"
                    :label="item.label"
                    :value="item.value"
                  />
                </el-select>
              </el-form-item>
              <el-form-item label="知识库">
                <el-select v-model="selectedKnowledgeBase" placeholder="请选择知识库">
                  <el-option
                    v-for="kb in knowledgeBases"
                    :key="kb.id"
                    :label="kb.kb_name"
                    :value="kb.kb_name"
                  />
                </el-select>
              </el-form-item>
            </el-form>
          </div>
          <deep-chat
            id="chat-element"
            avatars="true"
            :demo="true"
            style="
              margin-left: 15%;
              width: 80%;
              height: 100%;
              background-color: #f6f7f9;
              border: none;
            "
          >
          </deep-chat>
        </div>
      </div>
    </div>
  </div>

  <!--  先渲染 不能放在item里面-->
  <v-contextmenu ref="contextmenu">
    <v-contextmenu-item @click="handleEdit">修改</v-contextmenu-item>
    <v-contextmenu-item @click="handleDelete">删除</v-contextmenu-item>
  </v-contextmenu>

  <v-contextmenu ref="conversationMenu">
    <v-contextmenu-item @click="handleDeleteConversation">删除</v-contextmenu-item>
  </v-contextmenu>

  <el-dialog
    v-model="isShowConfigManagementDialog"
    :title="isEditMode ? '编辑配置' : '新建配置'"
    width="800px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    @close="handleConfigDialogClose"
  >
    <div style="height: 30vh; display: flex">
      <el-scrollbar style="width: 20%; border-right: 1px solid #ebeef5">
        <el-button type="primary" style="margin: 10px" @click="handleNewConfig">新建配置</el-button>
        <el-menu
          :default-active="activeConfigId"
          class="transparent-menu"
          @select="handleConfigSelect"
        >
          <el-menu-item
            v-for="config in configs"
            :key="config.config_id"
            :index="config.config_id as string"
          >
            {{ config.config_name }}
          </el-menu-item>
        </el-menu>
      </el-scrollbar>

      <el-scrollbar style="width: 70%; padding-left: 20px">
        <el-form :model="configManagementForm" label-width="120px">
          <el-form-item label="配置名称">
            <el-input
              v-model="configManagementForm.config_name"
              v-if="configManagementForm.platform !== 'LOCAL'"
            />
            <el-select
              v-model="configManagementForm.config_name"
              v-else
              placeholder="请选择配置名称"
              @change="syncLocalConfig"
            >
              <el-option label="MiniCPM-2B" value="MiniCPM-2B"></el-option>
              <el-option label="Qwen2-0.5B" value="Qwen2-0.5B"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="平台">
            <el-select
              v-model="configManagementForm.platform"
              placeholder="请选择平台"
              @change="handlePlatformChange"
            >
              <el-option label="OpenAI" value="OpenAI"></el-option>
              <el-option label="Anthropic" value="Anthropic"></el-option>
              <el-option label="Local" value="LOCAL"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="基础URL" v-if="configManagementForm.platform !== 'LOCAL'">
            <el-input v-model="configManagementForm.base_url" />
          </el-form-item>
          <el-form-item label="API密钥" v-if="configManagementForm.platform !== 'LOCAL'">
            <el-input v-model="configManagementForm.api_key" />
          </el-form-item>
          <el-form-item label="LLM模型">
            <template v-if="configManagementForm.platform === 'LOCAL'">
              <el-select v-model="configManagementForm.llm_model.model" @change="syncLocalConfig">
                <el-option label="MiniCPM-2B" value="MiniCPM-2B"></el-option>
                <el-option label="Qwen2-0.5B" value="Qwen2-0.5B"></el-option>
              </el-select>
            </template>
            <template v-else>
              <el-input v-model="configManagementForm.llm_model.model" />
            </template>
          </el-form-item>
        </el-form>
      </el-scrollbar>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button :disabled="isDeleteButtonDisabled" @click="handleDeleteConfig">删除</el-button>
        <el-button type="primary" :disabled="isSaveButtonDisabled" @click="handleSaveConfig">
          {{ isEditMode ? '更新' : '保存' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import 'deep-chat'

import { useRouter } from 'vue-router'
import type { DeepChat } from 'deep-chat'
import uploadIcon from '../assets/mingcute--tool-line.png'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Agent } from './type'
import { Signals } from 'deep-chat/dist/types/handler'
import { useToolConfig } from './toolConfig'
import { ModelConfig, useConfigManagement } from './configManagement'
import { JsonCollapse, MessageCollapse } from './customComponents'
import { Conversation, useConversation } from './conversationApi'
import { useConversationStore, useModelConfigStore } from '../store/store'

/*********************************** 知识库配置 ***********************************/

import { useKnowledgeBase } from './knowledgebase/kbapi'

const { knowledgeBases, fetchAllKnowledgeBases } = useKnowledgeBase()
const selectedKnowledgeBase = ref('')

// 知识库设置暂时不可用
// watch(selectedKnowledgeBase, (newKnowledgeBase) => {
//   localConversationConfig.value.knowledge_base = newKnowledgeBase
// })

/******************************************************************************/

/*********************************** onMounted初始化 ***********************************/
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { isNull } from '@pureadmin/utils'
import { clearMessageElement } from '@renderer/views/utils'

const selectedAgentTitle = ref<HTMLDivElement | null>(null)

onMounted(async () => {
  try {
    // 配置相关
    await fetchAllConfigs()
    if (useModelConfigStore().getConfigId() != '') {
      selectModel(
        configs.value.find((config) => config.config_id === useModelConfigStore().getConfigId())!
      )
    } else if (configs.value.length > 0 && configs.value[0].config_id) {
      selectModel(configs.value[0])
    }

    // 工具相关
    await fetchAvailableTools()

    // Fetch knowledge bases
    await fetchAllKnowledgeBases()

    // Agent 相关
    await fetchAgents()

    // 对话相关
    await fetchConversations()

    // 进入界面直接创建一个对话
    await createConversation(-1)

    // Deep Chat 初始化
    chatElementRef = document.getElementById('chat-element') as DeepChat

    if (chatElementRef) {
      chatElementRef.avatars = true
      chatElementRef.textInput = {
        placeholder: {
          text: '请输入你的问题...'
        }
      }
      chatElementRef.mixedFiles = {
        button: {
          position: 'inside-left'
        }
      }
    } else {
      console.error('Chat element not found')
    }
    console.log('All initialization completed successfully')

    chatElementRef.connect = {
      stream: { simulation: 6 },
      handler: async (body, signals: Signals) => {
        handleMessage(body, signals, chatElementRef as DeepChat)
      }
    }
  } catch (error) {
    console.error('Error during initialization:', error)
    ElMessage.error('初始化过程中发生错误，请刷新页面重试')
  }
  console.log(localConversationConfig.value)

  if (chatElementRef) {
    chatElementRef.onComponentRender = () => {
      ;() => {
        chatElementRef!.textInput = chatInputConfig()
      }
    }
  }

  if (chatElementRef) {
    let chatView: HTMLElement | null = null
    let newDiv: HTMLDivElement | null = null

    const createNewDiv = () => {
      if (chatView) {
        // 删除旧的 newDiv
        if (newDiv) {
          chatView.removeChild(newDiv)
        }

        // 创建新的 newDiv
        newDiv = document.createElement('div')
        newDiv.className = 'intro-panel'
        newDiv.style.position = 'absolute'
        newDiv.style.transform = 'translate(-50%, -50%)'
        newDiv.style.backgroundColor = '#e1e1e1'
        newDiv.style.borderRadius = '10px'
        newDiv.style.padding = '12px'
        newDiv.style.paddingBottom = '15px'
        newDiv.style.margin = '0'
        newDiv.style.maxWidth = '50%'
        newDiv.style.opacity = '0.3'
        newDiv.style.zIndex = '1000'

        // 计算并设置 newDiv 的位置
        const chatViewRect = chatView.getBoundingClientRect()
        const newDivRect = newDiv.getBoundingClientRect()

        newDiv.style.top = `${(chatViewRect.height - newDivRect.height) / 2}px`
        newDiv.style.left = `${(chatViewRect.width - newDivRect.width) / 2}px`

        // 将新的 newDiv 添加到 chatView
        chatView.appendChild(newDiv)
        updateIntroPanel(selectedAgent.value)
      }
    }

    const checkTextMessage = () => {
      const textMessage = chatElementRef!.shadowRoot!.querySelector('.text-message')
      if (newDiv) {
        newDiv.style.display = textMessage ? 'none' : 'block'
      }
    }

    chatElementRef.onComponentRender = () => {
      const shadowRoot = chatElementRef!.shadowRoot
      chatView = shadowRoot!.querySelector('#chat-view')

      if (chatView) {
        createNewDiv() // 初始化时创建新的 newDiv

        // 使用 MutationObserver 监视 chatView 的变化
        const observer = new MutationObserver((mutations) => {
          mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
              checkTextMessage()
            }
          })
        })

        observer.observe(chatView, { childList: true, subtree: true })
      }
    }

    // 监听窗口大小变化事件
    window.addEventListener('resize', createNewDiv)

    // 使用 ResizeObserver 监听 chatView 的尺寸变化
    if (chatView) {
      const resizeObserver = new ResizeObserver(createNewDiv)
      resizeObserver.observe(chatView)
    }
  }

  // 加载之前已选中的对话
  const tempConversation = useConversationStore().getCurrentConversation()
  if (tempConversation !== null) {
    handleSwitchConversation(tempConversation)
  }
})
// 确保在组件卸载时清除定时器

/******************************************************************************/

// ========================== Router and Component Setup ==========================
const router = useRouter()

//临时跳转到知识库管理界面
// router.push("/kbconfig");

let chatElementRef: DeepChat | null = null

const handleSelect = (index: string) => {
  console.log(`Selected menu item: ${index}`)
}

const defineCustomElementSafely = (name, constructor) => {
  if (!customElements.get(name)) {
    customElements.define(name, constructor)
  }
}

defineCustomElementSafely('json-collapse', JsonCollapse)
defineCustomElementSafely('message-collapse', MessageCollapse)
const toAgentConfig = () => {
  router.push('/agentconfig')
}
const toKBConfig = () => {
  router.push('/kbconfig')
}

/*********************************** 模型配置管理 ***********************************/
const {
  configs,
  activeConfigId,
  isShowConfigManagementDialog,
  configManagementForm,
  fetchAllConfigs,
  handleConfigSelect,
  handleSaveConfig,
  isDeleteButtonDisabled,
  isSaveButtonDisabled,
  isEditMode,
  handleDeleteConfig,
  handleNewConfig
} = useConfigManagement()

const handleConfigDialogClose = async () => {
  await fetchAllConfigs()

  if (
    chatSettings.value.config_id &&
    !configs.value.some((config) => config.config_id === chatSettings.value.config_id)
  ) {
    chatSettings.value.config_id = ''
    chatSettings.value.config_name = '未选择配置'
  }

  if (!chatSettings.value.config_id && configs.value.length > 0) {
    selectModel(configs.value[0])
  }
}

// Modified function to handle platform changes
const handlePlatformChange = (platform: string) => {
  if (platform === 'LOCAL') {
    configManagementForm.base_url = ''
    configManagementForm.api_key = ''
    configManagementForm.config_name = 'MiniCPM-2B'
    configManagementForm.llm_model.model = 'MiniCPM-2B'
  } else {
    // Reset to empty strings when switching from LOCAL to other platforms
    if (
      configManagementForm.config_name === 'MiniCPM-2B' ||
      configManagementForm.config_name === 'Qwen2-0.5B'
    ) {
      configManagementForm.config_name = ''
    }
    if (
      configManagementForm.llm_model.model === 'MiniCPM-2B' ||
      configManagementForm.llm_model.model === 'Qwen2-0.5B'
    ) {
      configManagementForm.llm_model.model = ''
    }
  }
}

// New function to synchronize config name and LLM model for LOCAL platform
const syncLocalConfig = (value: string) => {
  if (configManagementForm.platform === 'LOCAL') {
    configManagementForm.config_name = value
    configManagementForm.llm_model.model = value
  }
}

/******************************************************************************/

/*********************************** 对话配置 ***********************************/

//仅用于左上角的配置显示
const chatSettings = ref({
  config_id: '',
  config_name: ''
})

const selectModel = (selectConfig: ModelConfig) => {
  if (selectConfig) {
    chatSettings.value.config_id = selectConfig.config_id as string
    chatSettings.value.config_name = selectConfig.config_name
    localConversationConfig.value.config_id = Number.parseInt(selectConfig.config_id as string, 10)
    useModelConfigStore().setConfigId(selectConfig.config_id as string)
  }
}

/******************************************************************************/

// ========================== Tool Configuration ==========================
const { availableTools, selectedTools, fetchAvailableTools } = useToolConfig()

// ============================================================

// ========================== Message Handling ==========================

const agents = ref<Agent[]>([])

const selectedAgent = computed(() => {
  const agent = agents.value.find((agent) => agent.agent_id === selectedAgentId.value)
  return agent || null
})

watch(selectedAgent, (newAgent) => {
  updateIntroPanel(newAgent)
  if (selectedAgentTitle.value) {
    selectedAgentTitle.value.textContent =
      selectedAgentId.value === -1 || isAgentEnabled.value === false
        ? '未选择Agent'
        : newAgent?.agent_name || '未选择Agent'
  }
})

const updateIntroPanel = (agent: Agent | null) => {
  const introPanel = chatElementRef?.shadowRoot?.querySelector('.intro-panel')
  if (introPanel) {
    introPanel.innerHTML = `
    <div style="text-align: center; width: 100%;">
      <header style="margin-bottom: 12px;">
        <h2 style="font-size: 24px; margin: 0;">
          ${headerText.value}
        </h2>
      </header>
      <p style="font-size: 15px; line-height: 1.5; margin: 0 auto; max-width: 80%; white-space: pre-wrap;">
        ${
          !isAgentEnabled.value || selectedAgentId.value === -1
            ? '当前为直接对话模式，将与配置模型直接对话'
            : agent?.agent_abstract || `已选择Agent: ${agent?.agent_name}，但未提供描述`
        }
      </p>
    </div>
  `
  }
}

const headerText = computed(() => {
  if (selectedAgentId.value === -1 || !isAgentEnabled.value) {
    return '直接对话'
  }
  return selectedAgent.value?.agent_name || '未选择Agent'
})

const fetchAgents = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:7861/api/agent/list_agent')
    if (response.data.code === 200) {
      agents.value = response.data.data
    } else {
      ElMessage.error({
        message: response.data.msg
      })
    }
  } catch (error) {
    ElMessage.error({
      message: '获取Agent列表失败',
      type: 'error'
    })
    console.error('Failed to fetch agents:', error)
  }
}

const rightSelectedAgent = ref<Agent | null>(null)
const contextmenu = ref(null)

/*********************************** 创建对话以及消息处理等 ***********************************/
const {
  conversations,
  currentConversation,
  messages,
  createConversation,
  getConversations,
  deleteConversation,
  localConversationConfig,
  switchConversation,
  handleMessage
} = useConversation()

// 监听 conversation.title 变化并更新界面

watch(
  () => currentConversation.value,
  (newConversation) => {
    if (newConversation) {
      const index = conversations.value.findIndex(
        (c) => c.conversation_id === newConversation.conversation_id
      )
      if (index !== -1) {
        conversations.value[index] = newConversation
      }
    }
  },
  { deep: true }
)

const newConversationCreated = ref(false)

//表示右键点击的对话
const rightClickedConversation = ref<Conversation | null>(null)

// 处理对话右键点击事件
const handleConversationContextMenu = (event: MouseEvent, conversation: Conversation) => {
  event.preventDefault()
  rightClickedConversation.value = conversation
}

const fetchConversations = async () => {
  await getConversations()
}

const selectedAgentId = ref<number | null>(-1)

// 监听 agent 选择的变化
watch(selectedAgentId, (newAgentId) => {
  if (newAgentId !== -1) {
    const selectedAgent = agents.value.find((agent) => agent.agent_id === newAgentId)
    if (selectedAgent) {
      updateConfigFromAgent(selectedAgent)
    }
  }
})

// 更新配置
const updateConfigFromAgent = (agent: Agent) => {
  localConversationConfig.value.temperature = agent.temperature
  localConversationConfig.value.max_tokens = agent.max_tokens
  selectedTools.value = agent.tool_config
  isAgentEnabled.value = true
  localConversationConfig.value.agent_id = agent.agent_id as number

  // 如果agent有知识库配置，也更新知识库
  if (agent.kb_name && agent.kb_name.length > 0) {
    selectedKnowledgeBase.value = agent.kb_name[0] //TODO:这里可能需要修改
  }
}

watch(
  selectedTools,
  (newSelectedTools) => {
    localConversationConfig.value.tool_config = newSelectedTools
  },
  { deep: true }
)

const isAgentEnabled = computed({
  get: () => localConversationConfig.value.agent_id !== -1,
  set: (value) => {
    if (value) {
      // 启用 agent 时，使用当前选中的 agent_id
      if (!isNull(selectedAgentId.value)) {
        localConversationConfig.value.agent_id = selectedAgentId.value
        console.log(
          'localConversationConfig.value.agent_id:',
          localConversationConfig.value.agent_id
        )
      } else {
        ElMessage.error('未选中 Agent')
      }
    } else {
      // 禁用 agent 时，设置为 -1
      localConversationConfig.value.agent_id = -1
    }
  }
})

watch(isAgentEnabled, (newValue) => {
  console.log('isAgentEnabled 变化:', newValue)
  if (!newValue) {
    selectedAgentId.value = -1
  }
  updateIntroPanel(selectedAgent.value)
})

const handleSwitchConversation = (conversation: Conversation) => {
  if (chatElementRef) {
    switchConversation(conversation, chatElementRef)
    const agent = agents.value.find((agent) => agent.agent_id === conversation.agent_id)
    if (agent !== undefined) {
      updateIntroPanel(agent)
      selectedAgentId.value = agent.agent_id as number
    } else {
      ElMessage.error('当前对话的 Agent 已被删除，请重新选择 Agent 或创建新的对话')
      selectedAgentId.value = -1
    }
  } else {
    console.error('Chat element is not initialized')
    // Optionally, you can show an error message to the user
    ElMessage.error('聊天界面未初始化，请刷新页面重试')
  }
}

const handleOptionClick = async (event: MouseEvent, agent: Agent) => {
  console.log('左键点击：', agent)
  console.log('event:', event)
  try {
    await createConversation(agent.agent_id as number)
    selectedAgentId.value = agent.agent_id as number

    console.log('当前对话ID：', currentConversation.value?.conversation_id)
    updateConfigFromAgent(agent)
    localConversationConfig.value.temperature = agent.temperature
    localConversationConfig.value.max_tokens = agent.max_tokens

    // 更新 isAgentEnabled
    isAgentEnabled.value = true
    localConversationConfig.value.agent_id = agent.agent_id as number

    newConversationCreated.value = true
    chatElementRef!.clearMessages()
    clearMessageElement(chatElementRef!)

    // 强制更新 headerText
    nextTick(() => {
      updateIntroPanel(agent)
    })
    chatElementRef?.focusInput()
  } catch (e) {
    console.error(e)
    ElMessage.error('创建新对话失败')
  }
}

// 处理删除对话
const handleDeleteConversation = async () => {
  if (rightClickedConversation.value) {
    try {
      //如果删除的对话是当前对话则清空聊天界面
      if (
        rightClickedConversation.value.conversation_id ===
        currentConversation.value?.conversation_id
      ) {
        chatElementRef!.clearMessages()
        clearMessageElement(chatElementRef!)
      }

      // 如果删除的是当前对话，清空当前对话和消息
      console.log(
        'currentConversation.value?.conversation_id:',
        currentConversation.value?.conversation_id
      )
      console.log(
        'rightClickedConversation.value.conversation_id:',
        rightClickedConversation.value.conversation_id
      )
      if (
        currentConversation.value?.conversation_id ===
        rightClickedConversation.value.conversation_id
      ) {
        selectedAgentId.value = -1
        currentConversation.value = null
        messages.value = []
      }
      await deleteConversation(rightClickedConversation.value.conversation_id)

      await fetchConversations()
      ElMessage.success('对话删除成功')
    } catch (error) {
      console.error('删除对话失败:', error)
      ElMessage.error('删除对话失败')
    } finally {
      rightClickedConversation.value = null
    }
  }
}

/******************************************************************************/

/*********************************** Agent增删改查 ***********************************/
const handleEdit = () => {
  if (rightSelectedAgent.value) {
    router.push({
      path: '/agentconfig',
      query: { agentId: rightSelectedAgent.value.agent_id }
    })
  }
}

const handleDelete = async () => {
  if (rightSelectedAgent.value) {
    try {
      const response = await axios.delete(`http://127.0.0.1:7861/api/agent/delete_agent`, {
        headers: {
          accept: 'application/json',
          'Content-Type': 'application/json'
        },
        data: (rightSelectedAgent.value.agent_id as number).toString()
      })

      if (response.data.code === 200) {
        ElMessage.success({
          message: 'Agent删除成功'
        })
        agents.value = agents.value.filter(
          (agent) => agent.agent_id !== rightSelectedAgent.value!.agent_id
        )
      } else {
        ElMessage.error({
          message: response.data.msg
        })
      }
    } catch (error) {
      ElMessage.error({
        message: '删除Agent失败',
        type: 'error'
      })
      console.error('Failed to delete agent:', error)
    } finally {
      fetchAgents()
    }
  }
}

const handleContextMenu = (event: MouseEvent, agent: Agent) => {
  event.preventDefault()
  console.log('右键点击：', agent)
  rightSelectedAgent.value = agent
}
/******************************************************************************/
/*********************************** 未配置完毕禁止输入 ***********************************/

const chatInputConfig = () => {
  const isConfigMissing = isNaN(localConversationConfig.value.config_id)
  const isAgentMissing = isNaN(localConversationConfig.value.agent_id)

  return {
    disabled: isConfigMissing || isAgentMissing,
    placeholder: {
      text:
        isConfigMissing && isAgentMissing
          ? '请创建模型配置并新建/选择对话'
          : isConfigMissing
            ? '请创建模型配置'
            : isAgentMissing
              ? '请新建/选择对话'
              : '请输入你的问题...'
    }
  }
}

/******************************************************************************/
</script>

<style scoped>
/*
.agent-title {
  text-align: center;
  font-size: 1.2em;
  font-weight: bold;
  margin: 10px 0;
}
*/

.small-font {
  font-size: 0.9em; /* 调整字体大小 */
}

.transparent-menu {
  background-color: transparent;
}

.thumbnail {
  width: 32px;
  height: 32px;
}

.option-icon {
  position: absolute;
  right: 10px;
  display: none;
}

.el-menu-item:hover .option-icon {
  display: block;
}

.option-icon-img {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.options-popover {
  position: absolute;
  top: 30px;
  right: 10px;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.option-item {
  padding: 0px 10px;
  cursor: pointer;
}

.option-item:hover {
  background: #f0f0f0;
}

.option-item.delete {
  color: red;
}

.thumbnail {
  width: 32px;
  height: 32px;
}

:deep(.el-divider__text) {
  background-color: #f4f4f4;
}

.common-layout {
  height: 98vh;
  display: flex;
  flex-direction: row;
  overflow: hidden;
}

.aside-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 10%;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: #ffffff; /* Changed to white */
}

.el-scrollbar {
  height: 100%;
}

.aside-buttons {
  margin-top: auto;
  padding: 10px;
  background-color: #ffffff; /* Changed to white */
  cursor: pointer;
}

.aside-buttons div {
  text-align: center;
}

.main-container {
  display: flex;
  flex-direction: column;
  width: 90%;
  height: 100%;
}

.header-area {
  display: flex;
  align-items: center;
  justify-content: center; /* 新增 */
  width: 100%;
}

.horizontal-menu {
  flex: 1;
  width: 200px;
}

.chat-header {
  flex: 1;
  /*text-align: left;*/
  margin-left: 8%;
}

.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  overflow: hidden; /* 防止内容溢出 */
}

.chat-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  height: 100%;
  justify-content: flex-start;
  align-items: stretch;
  background-color: #f6f7f9;
}

.chat-controls {
  width: 200px;
  padding: 20px;
  background-color: #ffffff; /* Changed to white */
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
}

.horizontal-menu {
  font-weight: bold;
}

.agent-list {
  vertical-align: middle;
  font-weight: bold;
}

.box-card {
  padding-bottom: 20px;
  margin-bottom: 0px;
  background-color: #ffffff; /* Changed to white */
  border: transparent;
  box-shadow: none;
}

.card-header {
  text-align: center;
  font-size: 1.5em;
  font-weight: bold;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-top: -10px;
}

.align-middle {
  vertical-align: middle;
}

.el-divider {
  background-color: #ffffff;
}

:deep(.el-divider__text) {
  background-color: #ffffff;
}

.el-menu-vertical-demo:not(.el-menu--collapse) {
  background-color: transparent;
}

/* 设置菜单的自定义 CSS 变量 */
:deep(.conversation-menu) {
  --el-menu-active-color: #acd8ff; /* 更改为您喜欢的激活颜色 */
  --el-menu-hover-bg-color: #e6f7ff; /* 更改为您喜欢的悬停背景颜色 */
}

/* 设置激活菜单项的背景颜色 */
:deep(.conversation-menu .el-menu-item.is-active) {
  background-color: var(--el-menu-hover-bg-color);
}

/* 设置鼠标悬停时菜单项的背景颜色 */
:deep(.conversation-menu .el-menu-item:hover) {
  background-color: var(--el-menu-hover-bg-color);
}

/* 更改激活菜单项的文本颜色 */
:deep(.conversation-menu .el-menu-item.is-active) {
  color: var(--el-menu-active-color);
}

/* 为激活的菜单项添加左边框 */
:deep(.conversation-menu .el-menu-item.is-active) {
  border-left: 3px solid var(--el-menu-active-color);
}

/* 调整所有菜单项的左内边距 */
:deep(.conversation-menu .el-menu-item) {
  padding-left: 17px; /* 默认是 20px，我们减去 3px 以适应边框 */
}

/* 调整激活菜单项的左内边距 */
:deep(.conversation-menu .el-menu-item.is-active) {
  padding-left: 14px; /* 17px - 3px（边框宽度） */
}
</style>

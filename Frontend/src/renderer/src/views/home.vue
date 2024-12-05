<template>
  <div class="mp-shell" :class="{ 'is-empty': displayItems.length === 0 }">
    <!-- ================= 侧边栏 ================= -->
    <aside class="mp-sidebar">
      <div class="mp-brand">
        <span class="mp-brand-mark"></span>
        <span class="mp-brand-name">MindPilot</span>
      </div>

      <button class="mp-new-chat" @click="handleNewBlankConversation">
        <span class="mp-new-chat-icon">＋</span> 新对话
      </button>

      <div class="mp-section-label">智能体</div>
      <div class="mp-agent-list" v-contextmenu:contextmenu>
        <div
          v-for="agent in agents"
          :key="agent.agent_id"
          class="mp-agent-item"
          :class="{ active: agent.agent_id === selectedAgentId }"
          @click="handleOptionClick($event, agent)"
          @contextmenu="handleContextMenu($event, agent)"
        >
          <img :src="agent.avatar || uploadIcon" class="mp-agent-avatar" alt="" />
          <span class="mp-agent-name">{{ agent.agent_name }}</span>
        </div>
        <div v-if="agents.length === 0" class="mp-empty-hint">暂无智能体</div>
      </div>

      <div class="mp-section-label">对话</div>
      <div class="mp-conv-list" v-contextmenu:conversationMenu>
        <div
          v-for="conversation in [...conversations].reverse()"
          :key="conversation.conversation_id"
          class="mp-conv-item"
          :class="{ active: conversation.conversation_id === currentConversation?.conversation_id }"
          @click="handleSwitchConversation(conversation)"
          @contextmenu="handleConversationContextMenu($event, conversation)"
        >
          <span class="mp-conv-title">{{ conversation.title || '新对话' }}</span>
        </div>
        <div v-if="conversations.length === 0" class="mp-empty-hint">暂无历史记录</div>
      </div>

      <div class="mp-sidebar-footer">
        <div class="mp-footer-link" @click="toKBConfig">知识库管理</div>
        <div class="mp-footer-link" @click="isShowConfigManagementDialog = true">模型配置</div>
        <div class="mp-footer-link" @click="toAgentConfig">创建智能体</div>
      </div>
    </aside>

    <!-- ================= 主区域 ================= -->
    <main class="mp-main">
      <!-- 顶栏 -->
      <header class="mp-topbar">
        <div class="mp-topbar-left">
          <el-dropdown trigger="click" @command="handleConfigCommand">
            <button class="mp-model-btn">
              {{ chatSettings.config_name || '选择模型' }}
              <span class="mp-caret">▾</span>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="config in configs"
                  :key="config.config_id"
                  :command="config.config_id"
                >
                  {{ config.config_name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="mp-topbar-right">
          <span v-if="selectedAgentId !== -1" class="mp-agent-hint">{{ headerText }}</span>
        </div>
      </header>

      <!-- 消息时间线 -->
      <div ref="scrollRef" class="mp-timeline">
        <!-- 空状态 -->
        <div v-if="displayItems.length === 0" class="mp-hero mp-fade-up">
          <h1 class="mp-hero-title">
            {{ selectedAgentId === -1 ? '有什么可以帮忙的？' : headerText }}
          </h1>
          <p v-if="selectedAgentId !== -1 && selectedAgent?.agent_abstract" class="mp-hero-sub">
            {{ selectedAgent.agent_abstract }}
          </p>
        </div>

        <!-- 消息列表 -->
        <div v-for="item in displayItems" :key="item.id" class="mp-msg-row mp-fade-up">
          <!-- 用户消息 -->
          <div v-if="item.kind === 'user'" class="mp-user-bubble">{{ item.text }}</div>

          <!-- 思考过程 -->
          <div v-else-if="item.kind === 'thought'" class="mp-step">
            <div class="mp-step-head" @click="toggleCollapse(item.id)">
              <span class="mp-step-icon">💭</span>
              <span class="mp-step-label">思考过程</span>
              <span class="mp-step-arrow" :class="{ open: !collapsed[item.id] }">▾</span>
            </div>
            <div v-show="!collapsed[item.id]" class="mp-step-body thought-body">{{ item.text }}</div>
          </div>

          <!-- 工具调用 -->
          <div v-else-if="item.kind === 'tool'" class="mp-step">
            <div class="mp-step-head" @click="toggleCollapse(item.id)">
              <span class="mp-step-icon">{{ toolIcon(item.toolName) }}</span>
              <span class="mp-step-label">{{ toolLabel(item.toolName) }}</span>
              <span class="mp-step-arrow" :class="{ open: !collapsed[item.id] }">▾</span>
            </div>
            <div v-show="!collapsed[item.id]" class="mp-step-body">
              <pre class="mono mp-json">{{ prettyJson(item.json) }}</pre>
            </div>
          </div>

          <!-- 助手文本 -->
          <div v-else class="mp-assistant">
            <div class="mp-assistant-text" v-html="renderMd(item.text)"></div>
          </div>
        </div>

        <!-- 执行中指示器 -->
        <div v-if="sending" class="mp-working mp-fade-up">
          <span class="mp-working-dot"></span>
          <span>{{ sendingStatus }}…</span>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="mp-composer-wrap">
        <div class="mp-composer" :class="{ disabled: inputDisabled }">
          <textarea
            v-model="inputText"
            class="mp-input"
            :placeholder="inputPlaceholder"
            :disabled="inputDisabled"
            rows="1"
            @keydown.enter.exact.prevent="handleSend"
            @input="autoGrow"
          ></textarea>
          <div class="mp-composer-bar">
            <div class="mp-composer-left">
              <el-popover placement="top-start" width="280" trigger="click">
                <template #reference>
                  <button class="mp-mini-btn" title="运行参数">⚙</button>
                </template>
                <div class="mp-params">
                  <div class="mp-params-row">
                    <span>温度 {{ localConversationConfig.temperature }}</span>
                    <el-slider
                      v-model="localConversationConfig.temperature"
                      :min="0.1"
                      :max="1"
                      :step="0.1"
                    />
                  </div>
                  <div class="mp-params-row">
                    <span>最大 Token</span>
                    <el-input-number
                      v-model="localConversationConfig.max_tokens"
                      :min="1"
                      :max="8192"
                      size="small"
                    />
                  </div>
                  <div v-if="selectedAgentId !== -1" class="mp-params-row">
                    <span>工具</span>
                    <el-select
                      v-model="selectedTools"
                      multiple
                      collapse-tags
                      collapse-tags-tooltip
                      size="small"
                      style="width: 100%"
                    >
                      <el-option
                        v-for="t in availableTools"
                        :key="t.value"
                        :label="t.label"
                        :value="t.value"
                      />
                    </el-select>
                  </div>
                </div>
              </el-popover>
              <span v-if="selectedTools.length > 0" class="mp-tool-count">
                已启用 {{ selectedTools.length }} 个工具
              </span>
            </div>
            <button
              class="mp-send"
              :disabled="inputDisabled || !inputText.trim() || sending"
              @click="handleSend"
            >
              <span v-if="!sending">↑</span>
              <span v-else class="mp-send-loading">…</span>
            </button>
          </div>
        </div>
        <div class="mp-composer-hint">MindPilot 也可能会犯错，请核查重要信息。</div>
      </div>
    </main>

    <!-- 右键菜单 -->
    <v-contextmenu ref="contextmenu">
      <v-contextmenu-item @click="handleEdit">修改</v-contextmenu-item>
      <v-contextmenu-item @click="handleDelete">删除</v-contextmenu-item>
    </v-contextmenu>

    <v-contextmenu ref="conversationMenu">
      <v-contextmenu-item @click="handleDeleteConversation">删除</v-contextmenu-item>
    </v-contextmenu>

    <!-- 模型配置管理对话框 -->
    <el-dialog
      v-model="isShowConfigManagementDialog"
      :title="isEditMode ? '编辑配置' : '新建配置'"
      width="800px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      @close="handleConfigDialogClose"
    >
      <div style="height: 32vh; display: flex">
        <el-scrollbar style="width: 24%; border-right: 1px solid var(--mp-border)">
          <el-button type="primary" style="margin: 10px" @click="handleNewConfig"
            >新建配置</el-button
          >
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

        <el-scrollbar style="width: 76%; padding-left: 20px">
          <el-form :model="configManagementForm" label-width="100px">
            <el-form-item label="配置名称">
              <el-input
                v-if="configManagementForm.platform !== 'LOCAL'"
                v-model="configManagementForm.config_name"
              />
              <el-select
                v-else
                v-model="configManagementForm.config_name"
                placeholder="请选择配置名称"
                @change="syncLocalConfig"
              >
                <el-option label="MiniCPM-2B" value="MiniCPM-2B"></el-option>
                <el-option label="Qwen2-0.5B" value="Qwen2-0.5B"></el-option>
                <el-option label="Qwen2.5-72B-Instruct" value="Qwen2.5-72B-Instruct"></el-option>
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
            <el-form-item v-if="configManagementForm.platform !== 'LOCAL'" label="基础URL">
              <el-input v-model="configManagementForm.base_url" />
            </el-form-item>
            <el-form-item v-if="configManagementForm.platform !== 'LOCAL'" label="API密钥">
              <el-input v-model="configManagementForm.api_key" type="password" show-password />
            </el-form-item>
            <el-form-item label="LLM模型">
              <el-select
                v-if="configManagementForm.platform === 'LOCAL'"
                v-model="configManagementForm.llm_model.model"
                @change="syncLocalConfig"
              >
                <el-option label="MiniCPM-2B" value="MiniCPM-2B"></el-option>
                <el-option label="Qwen2-0.5B" value="Qwen2-0.5B"></el-option>
                <el-option label="Qwen2.5-72B-Instruct" value="Qwen2.5-72B-Instruct"></el-option>
              </el-select>
              <el-input v-else v-model="configManagementForm.llm_model.model" />
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
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import uploadIcon from '../assets/mingcute--tool-line.png'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { Agent } from './type'
import { useToolConfig } from './toolConfig'
import { ModelConfig, useConfigManagement } from './configManagement'
import { extractFirstJSON } from './utils'
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

const API_BASE = 'http://127.0.0.1:7861/api'

/*********************************** 类型 ***********************************/
interface Conversation {
  conversation_id: string
  title: string
  created_at: string
  updated_at: string
  is_summarized: boolean
  agent_id: number
}

interface BackendMessage {
  message_id: number
  agent_status: number
  role: string
  text: string
  timestamp: string
}

interface DisplayItem {
  id: number
  kind: 'user' | 'text' | 'thought' | 'tool'
  text?: string
  toolName?: string
  json?: string
}

/*********************************** 状态 ***********************************/
const router = useRouter()
const agents = ref<Agent[]>([])
const conversations = ref<Conversation[]>([])
const currentConversation = ref<Conversation | null>(null)
const displayItems = ref<DisplayItem[]>([])
const selectedAgentId = ref<number>(-1)
const inputText = ref('')
const sending = ref(false)
const elapsed = ref(0)
const collapsed = reactive<Record<number, boolean>>({})
const scrollRef = ref<HTMLDivElement | null>(null)
let itemSeq = 0
let timer: ReturnType<typeof setInterval> | null = null

const { availableTools, selectedTools, fetchAvailableTools } = useToolConfig()

const localConversationConfig = ref({
  agent_id: -1 as number,
  config_id: NaN as number,
  tool_config: [] as string[],
  temperature: 0.8,
  max_tokens: 4096
})

const selectedAgent = computed(
  () => agents.value.find((a) => a.agent_id === selectedAgentId.value) || null
)

const isAgentEnabled = computed(() => localConversationConfig.value.agent_id !== -1)

const headerText = computed(() => {
  if (selectedAgentId.value === -1 || !isAgentEnabled.value) return '直接对话'
  return selectedAgent.value?.agent_name || '未选择 Agent'
})

const sendingStatus = computed(() =>
  selectedAgentId.value !== -1 && isAgentEnabled.value ? 'Agent 执行中' : '思考中'
)

const inputDisabled = computed(
  () => isNaN(localConversationConfig.value.config_id) || !currentConversation.value
)

const inputPlaceholder = computed(() => {
  if (isNaN(localConversationConfig.value.config_id)) return '请先在「模型配置」中创建并选择一个配置…'
  if (!currentConversation.value) return '请新建或选择一个对话…'
  if (sending.value) return '正在生成回复…'
  return '给 MindPilot 下达任务…'
})

/*********************************** 初始化 ***********************************/
onMounted(async () => {
  try {
    await fetchAllConfigs()
    if (configs.value.length > 0 && configs.value[0].config_id) {
      selectModel(configs.value[0])
    }
    await fetchAvailableTools()
    await fetchAgents()
    await fetchConversations()
    if (!currentConversation.value) {
      await createConversation(-1)
    }
  } catch (e) {
    console.error('初始化失败:', e)
    ElMessage.error('初始化失败，请确认后端服务已启动（127.0.0.1:7861）')
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

/*********************************** 工具函数 ***********************************/
const scrollToBottom = () => {
  nextTick(() => {
    if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
  })
}

const toggleCollapse = (id: number) => {
  collapsed[id] = !collapsed[id]
}

const toolIcon = (name?: string) => {
  const map: Record<string, string> = {
    search_internet: '🌐',
    search_local_knowledgebase: '📚',
    weather_check: '☁',
    calculate: '∑',
    arxiv: '📄',
    shell: '❯',
    wolfram: 'Ω'
  }
  return map[name || ''] || '⚙'
}

const toolLabel = (name?: string) => {
  const map: Record<string, string> = {
    search_internet: '已搜索网络',
    search_local_knowledgebase: '已检索知识库',
    weather_check: '已查询天气',
    calculate: '已完成计算',
    arxiv: '已检索论文',
    shell: '已执行命令',
    wolfram: '已调用 Wolfram'
  }
  return map[name || ''] || `已调用工具 ${name || ''}`
}

const prettyJson = (json?: string) => {
  if (!json) return ''
  try {
    return JSON.stringify(JSON.parse(json), null, 2)
  } catch {
    return json
  }
}

/** 轻量 Markdown 渲染：先转义再处理加粗/行内代码，防注入 */
const escapeHtml = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

const renderMd = (text?: string) => {
  if (!text) return ''
  return escapeHtml(text)
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code class="mono mp-inline-code">$1</code>')
}

/** 后端消息数组 → 展示项（对齐旧版 deep-chat 的渲染规则） */
const mapMessages = (msgs: BackendMessage[], appendUser?: string) => {
  const items: DisplayItem[] = []
  if (appendUser !== undefined) {
    items.push({ id: ++itemSeq, kind: 'user', text: appendUser })
  }
  msgs.forEach((m, i) => {
    const isLast = i === msgs.length - 1
    if (m.role === 'user') {
      if (appendUser === undefined) items.push({ id: ++itemSeq, kind: 'user', text: m.text })
      return
    }
    if (m.agent_status === 7) {
      const id = ++itemSeq
      collapsed[id] = true
      items.push({ id, kind: 'thought', text: m.text })
      return
    }
    const json = m.text ? extractFirstJSON(m.text) : null
    if (m.agent_status === 3 && json && json.action && json.action !== 'Final Answer') {
      const id = ++itemSeq
      collapsed[id] = true
      items.push({ id, kind: 'tool', toolName: json.action, json: JSON.stringify(json) })
      return
    }
    if (json && json.action === 'Final Answer') {
      items.push({ id: ++itemSeq, kind: 'text', text: json.action_input })
      return
    }
    if (m.agent_status === -1 || isLast || m.text) {
      items.push({ id: ++itemSeq, kind: 'text', text: m.text })
    }
  })
  return items
}

const autoGrow = (e: Event) => {
  const el = e.target as HTMLTextAreaElement
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}

/*********************************** Agent 相关 ***********************************/
const fetchAgents = async () => {
  try {
    const response = await axios.get(`${API_BASE}/agent/list_agent`)
    if (response.data.code === 200) {
      agents.value = response.data.data
    }
  } catch (e) {
    console.error('获取Agent列表失败:', e)
  }
}

const updateConfigFromAgent = (agent: Agent) => {
  localConversationConfig.value.temperature = agent.temperature
  localConversationConfig.value.max_tokens = agent.max_tokens
  selectedTools.value = agent.tool_config
  localConversationConfig.value.agent_id = agent.agent_id as number
}

const handleOptionClick = async (_event: MouseEvent, agent: Agent) => {
  try {
    await createConversation(agent.agent_id as number)
    selectedAgentId.value = agent.agent_id as number
    updateConfigFromAgent(agent)
    displayItems.value = []
  } catch (e) {
    console.error(e)
    ElMessage.error('创建新对话失败')
  }
}

const rightSelectedAgent = ref<Agent | null>(null)
const contextmenu = ref(null)

const handleContextMenu = (event: MouseEvent, agent: Agent) => {
  event.preventDefault()
  rightSelectedAgent.value = agent
}

const handleEdit = () => {
  if (rightSelectedAgent.value) {
    router.push({ path: '/agentconfig', query: { agentId: rightSelectedAgent.value.agent_id } })
  }
}

const handleDelete = async () => {
  if (!rightSelectedAgent.value) return
  try {
    const response = await axios.delete(`${API_BASE}/agent/delete_agent`, {
      headers: { accept: 'application/json', 'Content-Type': 'application/json' },
      data: (rightSelectedAgent.value.agent_id as number).toString()
    })
    if (response.data.code === 200) {
      ElMessage.success('Agent删除成功')
      agents.value = agents.value.filter((a) => a.agent_id !== rightSelectedAgent.value!.agent_id)
      if (selectedAgentId.value === rightSelectedAgent.value.agent_id) {
        selectedAgentId.value = -1
        localConversationConfig.value.agent_id = -1
      }
    } else {
      ElMessage.error(response.data.msg)
    }
  } catch (e) {
    ElMessage.error('删除Agent失败')
  } finally {
    rightSelectedAgent.value = null
  }
}

/*********************************** 对话相关 ***********************************/
const createConversation = async (agent_id: number) => {
  const response = await axios.post(`${API_BASE}/conversation`, agent_id)
  const conv: Conversation = response.data.data
  currentConversation.value = conv
  conversations.value.push(conv)
  localConversationConfig.value.agent_id = agent_id
  return conv
}

const fetchConversations = async () => {
  try {
    const response = await axios.get(`${API_BASE}/conversations`)
    conversations.value = response.data.data || []
  } catch (e) {
    console.error('获取对话列表失败:', e)
  }
}

const handleNewBlankConversation = async () => {
  try {
    await createConversation(-1)
    selectedAgentId.value = -1
    displayItems.value = []
  } catch (e) {
    ElMessage.error('创建新对话失败')
  }
}

const handleSwitchConversation = async (conversation: Conversation) => {
  try {
    const response = await axios.get(`${API_BASE}/conversation/${conversation.conversation_id}`)
    const detail = response.data.data
    currentConversation.value = conversation
    localConversationConfig.value.agent_id = conversation.agent_id

    const agent = agents.value.find((a) => a.agent_id === conversation.agent_id)
    if (agent) {
      selectedAgentId.value = agent.agent_id as number
      updateConfigFromAgent(agent)
    } else if (conversation.agent_id !== -1) {
      selectedAgentId.value = -1
      ElMessage.warning('该对话的 Agent 已被删除')
    } else {
      selectedAgentId.value = -1
    }
    displayItems.value = mapMessages(detail.messages || [])
    scrollToBottom()
  } catch (e) {
    console.error('切换对话失败:', e)
    ElMessage.error('加载对话失败')
  }
}

const rightClickedConversation = ref<Conversation | null>(null)
const conversationMenu = ref(null)

const handleConversationContextMenu = (event: MouseEvent, conversation: Conversation) => {
  event.preventDefault()
  rightClickedConversation.value = conversation
}

const handleDeleteConversation = async () => {
  if (!rightClickedConversation.value) return
  try {
    await axios.delete(`${API_BASE}/conversation/${rightClickedConversation.value.conversation_id}`)
    conversations.value = conversations.value.filter(
      (c) => c.conversation_id !== rightClickedConversation.value!.conversation_id
    )
    if (currentConversation.value?.conversation_id === rightClickedConversation.value.conversation_id) {
      currentConversation.value = null
      displayItems.value = []
      selectedAgentId.value = -1
    }
    ElMessage.success('对话删除成功')
  } catch (e) {
    ElMessage.error('删除对话失败')
  } finally {
    rightClickedConversation.value = null
  }
}

/*********************************** 发送消息 ***********************************/
const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || sending.value || !currentConversation.value) return

  inputText.value = ''
  sending.value = true
  elapsed.value = 0
  timer = setInterval(() => elapsed.value++, 1000)
  displayItems.value.push({ id: ++itemSeq, kind: 'user', text })
  scrollToBottom()

  try {
    const response = await axios.post(
      `${API_BASE}/conversation/${currentConversation.value.conversation_id}/messages`,
      {
        role: 'user',
        agent_id: localConversationConfig.value.agent_id,
        config_id: localConversationConfig.value.config_id,
        text,
        tool_config: selectedTools.value,
        temperature: localConversationConfig.value.temperature,
        max_tokens: localConversationConfig.value.max_tokens
      },
      { headers: { accept: 'application/json', 'Content-Type': 'application/json' } }
    )
    if (response.data.code === 200) {
      displayItems.value.push(...mapMessages(response.data.data || []))
      // 刷新标题等信息
      const detail = await axios.get(
        `${API_BASE}/conversation/${currentConversation.value.conversation_id}`
      )
      const idx = conversations.value.findIndex(
        (c) => c.conversation_id === currentConversation.value!.conversation_id
      )
      if (idx !== -1) {
        conversations.value[idx] = { ...conversations.value[idx], ...detail.data.data }
        currentConversation.value = conversations.value[idx]
      }
    } else {
      ElMessage.error(response.data.msg || '发送失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('发送消息时发生错误，请重试')
  } finally {
    sending.value = false
    if (timer) {
      clearInterval(timer)
      timer = null
    }
    scrollToBottom()
  }
}

watch(selectedTools, (v) => (localConversationConfig.value.tool_config = v), { deep: true })

/*********************************** 模型配置 ***********************************/
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

const chatSettings = ref({ config_id: '', config_name: '' })

const selectModel = (config: ModelConfig) => {
  if (!config) return
  chatSettings.value.config_id = config.config_id as string
  chatSettings.value.config_name = config.config_name
  localConversationConfig.value.config_id = Number.parseInt(config.config_id as string, 10)
}

const handleConfigCommand = (configId: string) => {
  const config = configs.value.find((c) => c.config_id === configId)
  if (config) selectModel(config)
}

const handleConfigDialogClose = async () => {
  await fetchAllConfigs()
  if (
    chatSettings.value.config_id &&
    !configs.value.some((c) => c.config_id === chatSettings.value.config_id)
  ) {
    chatSettings.value.config_id = ''
    chatSettings.value.config_name = ''
  }
  if (!chatSettings.value.config_id && configs.value.length > 0) {
    selectModel(configs.value[0])
  }
}

const handlePlatformChange = (platform: string) => {
  if (platform === 'LOCAL') {
    configManagementForm.base_url = ''
    configManagementForm.api_key = ''
    configManagementForm.config_name = 'MiniCPM-2B'
    configManagementForm.llm_model.model = 'MiniCPM-2B'
  } else {
    if (['MiniCPM-2B', 'Qwen2-0.5B'].includes(configManagementForm.config_name)) {
      configManagementForm.config_name = ''
    }
    if (['MiniCPM-2B', 'Qwen2-0.5B'].includes(configManagementForm.llm_model.model)) {
      configManagementForm.llm_model.model = ''
    }
  }
}

const syncLocalConfig = (value: string) => {
  if (configManagementForm.platform === 'LOCAL') {
    configManagementForm.config_name = value
    configManagementForm.llm_model.model = value
  }
}

/*********************************** 路由跳转 ***********************************/
const toAgentConfig = () => router.push('/agentconfig')
const toKBConfig = () => router.push('/kbconfig')
</script>

<style scoped>
.mono {
  font-family: var(--mp-font-mono);
}

/* ================= 布局骨架 ================= */
.mp-shell {
  display: flex;
  height: 100vh;
  background: var(--mp-bg-0);
  overflow: hidden;
}

/* ================= 侧边栏 ================= */
.mp-sidebar {
  width: var(--mp-sidebar-w);
  min-width: var(--mp-sidebar-w);
  background: var(--mp-bg-1);
  display: flex;
  flex-direction: column;
  padding: 10px 12px;
}

.mp-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 8px 16px;
}

.mp-brand-mark {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--mp-text-0);
  position: relative;
}

.mp-brand-mark::after {
  content: '';
  position: absolute;
  inset: 6px;
  border-radius: 50%;
  background: var(--mp-bg-1);
}

.mp-brand-name {
  font-weight: 600;
  font-size: 15px;
}

.mp-new-chat {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 10px;
  margin-bottom: 10px;
  background: transparent;
  color: var(--mp-text-0);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.12s;
  text-align: left;
}

.mp-new-chat:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mp-new-chat-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid var(--mp-border);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: var(--mp-text-1);
}

.mp-section-label {
  font-size: 12px;
  color: var(--mp-text-2);
  padding: 10px 10px 4px;
}

.mp-agent-list {
  max-height: 30%;
  overflow-y: auto;
}

.mp-agent-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--mp-text-0);
  transition: background 0.12s;
}

.mp-agent-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mp-agent-item.active {
  background: rgba(255, 255, 255, 0.09);
}

.mp-agent-avatar {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  object-fit: cover;
  opacity: 0.8;
}

.mp-agent-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.mp-conv-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.mp-conv-item {
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--mp-text-0);
  transition: background 0.12s;
}

.mp-conv-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mp-conv-item.active {
  background: rgba(255, 255, 255, 0.09);
}

.mp-conv-title {
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.mp-empty-hint {
  padding: 8px 10px;
  color: var(--mp-text-2);
  font-size: 12px;
}

.mp-sidebar-footer {
  padding-top: 6px;
}

.mp-footer-link {
  padding: 8px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: var(--mp-text-1);
  font-size: 13px;
  transition: background 0.12s;
}

.mp-footer-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--mp-text-0);
}

/* ================= 主区域 ================= */
.mp-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.mp-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
}

.mp-topbar-left {
  display: flex;
  align-items: center;
}

.mp-model-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  color: var(--mp-text-0);
  padding: 7px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: background 0.12s;
}

.mp-model-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.mp-caret {
  font-size: 10px;
  color: var(--mp-text-2);
}

.mp-agent-hint {
  font-size: 13px;
  color: var(--mp-text-2);
}

/* ================= 消息时间线 ================= */
.mp-timeline {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mp-msg-row {
  width: 100%;
  max-width: 760px;
  padding: 0 24px;
  margin-bottom: 6px;
}

/* 空状态 */
.mp-hero {
  margin: auto;
  text-align: center;
  padding: 40px;
}

/* 空状态时 Hero + 输入框整体垂直居中（ChatGPT 式首屏） */
.mp-shell.is-empty .mp-timeline {
  flex: none;
  width: 100%;
  margin-top: auto;
  padding: 0;
}

.mp-shell.is-empty .mp-hero {
  margin: 0;
  padding: 20px;
}

.mp-shell.is-empty .mp-composer-wrap {
  margin-bottom: auto;
  padding-top: 0;
}

.mp-hero-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 12px;
  color: var(--mp-text-0);
}

.mp-hero-sub {
  color: var(--mp-text-2);
  font-size: 14px;
  max-width: 420px;
  margin: 0 auto;
  line-height: 1.6;
}

/* 用户气泡 */
.mp-user-bubble {
  margin: 18px 0 6px auto;
  width: fit-content;
  max-width: 70%;
  background: var(--mp-bg-2);
  border-radius: 24px;
  padding: 10px 18px;
  color: var(--mp-text-0);
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Agent 步骤（极简行式） */
.mp-step {
  margin: 2px 0;
  border-radius: 10px;
}

.mp-step-head {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px 6px 4px;
  cursor: pointer;
  user-select: none;
  border-radius: 8px;
  color: var(--mp-text-2);
}

.mp-step-head:hover {
  color: var(--mp-text-1);
}

.mp-step-icon {
  font-size: 13px;
  opacity: 0.75;
}

.mp-step-label {
  font-size: 13px;
}

.mp-step-arrow {
  font-size: 10px;
  color: var(--mp-text-2);
  transition: transform 0.2s;
}

.mp-step-arrow.open {
  transform: rotate(180deg);
}

.mp-step-body {
  margin: 2px 0 8px 10px;
  padding: 4px 0 4px 16px;
  border-left: 1px solid var(--mp-border);
}

.thought-body {
  color: var(--mp-text-2);
  font-size: 13px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.mp-json {
  margin: 0;
  font-size: 12px;
  color: var(--mp-text-2);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow-y: auto;
}

/* 助手文本 */
.mp-assistant {
  padding: 4px 0 10px;
}

.mp-assistant-text {
  color: var(--mp-text-0);
  line-height: 1.8;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 15px;
}

.mp-assistant-text :deep(strong) {
  font-weight: 600;
}

.mp-assistant-text :deep(.mp-inline-code) {
  background: var(--mp-bg-2);
  border-radius: 4px;
  padding: 1px 5px;
  font-size: 13px;
}

/* 执行中 */
.mp-working {
  width: 100%;
  max-width: 760px;
  padding: 8px 24px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--mp-text-2);
  font-size: 13px;
}

.mp-working-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--mp-text-0);
  animation: mp-pulse 1.1s infinite;
}

/* ================= 输入区 ================= */
.mp-composer-wrap {
  padding: 8px 24px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mp-composer {
  width: 100%;
  max-width: 760px;
  background: var(--mp-bg-2);
  border: none;
  border-radius: 28px;
  padding: 14px 16px 10px;
}

.mp-composer.disabled {
  opacity: 0.55;
}

.mp-input {
  width: 100%;
  background: transparent;
  border: none;
  outline: none;
  resize: none;
  color: var(--mp-text-0);
  font-family: var(--mp-font-sans);
  font-size: 15px;
  line-height: 1.6;
  max-height: 200px;
}

.mp-input::placeholder {
  color: var(--mp-text-2);
}

.mp-composer-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.mp-composer-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.mp-mini-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: transparent;
  border: 1px solid var(--mp-border);
  color: var(--mp-text-2);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.mp-mini-btn:hover {
  color: var(--mp-text-0);
  background: rgba(255, 255, 255, 0.06);
}

.mp-tool-count {
  font-size: 12px;
  color: var(--mp-text-2);
}

.mp-send {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: #ececec;
  color: #212121;
  font-size: 15px;
  cursor: pointer;
  transition: opacity 0.15s;
}

.mp-send:hover:not(:disabled) {
  opacity: 0.85;
}

.mp-send:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: var(--mp-text-2);
  cursor: not-allowed;
}

.mp-send-loading {
  animation: mp-blink 1s infinite;
}

.mp-composer-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--mp-text-2);
}

/* 参数弹层 */
.mp-params {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.mp-params-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: var(--mp-text-1);
}

.transparent-menu {
  background: transparent;
  border-right: none;
}
</style>

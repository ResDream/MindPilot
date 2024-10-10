<template>
  <div class="agentconfig-layout">
    <el-container class="full-height">
      <el-header class="header">
        <div class="left-icons">
          <el-button class="back-button" type="text" @click="goBack">
            <Icon
              icon="weui:back-filled"
              width="40"
              height="40"
              style="color: #4d4d4d"
              class="back-icon"
            />
            <!--            <img :src="backButton" alt="Back" class="back-icon" />-->
          </el-button>
          <el-avatar :size="50" :src="avatarIcon" />
        </div>
        <div class="config-sub-menu horizontal-menu" style="left: 50%; position: absolute">
          <el-dropdown @command="selectDebugModel">
            <span class="el-dropdown-link">
              {{ debugConfigSettings.config_name || '未选择配置' }}
              <el-icon class="el-icon--right"><arrow-down /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  v-for="config in configs"
                  :key="config.config_id"
                  :command="config"
                >
                  {{ config.config_name }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <div class="right-buttons">
          <el-button
            class="config-button delete-config-button"
            type="primary"
            plain
            @click="deleteConfig"
            >删除
          </el-button>
          <el-button
            class="config-button save-config-button"
            type="danger"
            plain
            @click="saveConfig"
            >发布
          </el-button>
        </div>
      </el-header>
      <el-container class="content-container">
        <div style="width: 50%" class="config-menu">
          <div class="config-title">配置智能体</div>
          <el-form :model="agentForm" label-position="top" class="config-form">
            <el-form-item label="图标">
              <el-avatar class="agent-avatar" :size="50" :src="avatarIcon" @click="onUploadIcon" />
              <div class="el-upload__tip">&nbsp;&nbsp; 只能上传jpg/png文件，且不超过 1 mb</div>
            </el-form-item>
            <el-form-item label="名称">
              <el-input v-model="agentForm.agent_name" placeholder="命名你的工具"></el-input>
            </el-form-item>
            <el-form-item label="简介">
              <el-input
                v-model="agentForm.agent_abstract"
                type="textarea"
                placeholder="一句话介绍你的工具"
              ></el-input>
            </el-form-item>
            <el-form-item label="配置信息">
              <el-input
                v-model="agentForm.agent_info"
                type="textarea"
                :placeholder="configPlaceHolder"
                rows="4"
              ></el-input>
            </el-form-item>
            <el-form-item label="能力配置">
              <el-select v-model="selectedCapabilities" multiple placeholder="选择能力">
                <el-option
                  v-for="item in capabilities"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                >
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="自定义能力">
              <div
                style="
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  width: 100%;
                "
              >
                <span class="config-tips">让智能体调用外部AP来实现复杂功能</span>
                <el-button plain @click="createTool">自建插件</el-button>
              </div>
            </el-form-item>
            <el-form-item label="温度">
              <span class="temperature-tips config-tips"
                >温度越高，回答越随机，温度越低，回答越固定</span
              >
              <el-slider
                v-model="temperatureValue"
                :min="0.1"
                :max="1"
                :step="0.1"
                show-input
              ></el-slider>
            </el-form-item>
            <el-form-item label="最大Token">
              <div
                style="
                  display: flex;
                  align-items: center;
                  justify-content: space-between;
                  width: 100%;
                "
              >
                <span class="config-tips">模型最大输出长度</span>
                <el-input-number
                  v-model="agentForm.max_tokens"
                  :min="1"
                  placeholder="输入最大长度"
                ></el-input-number>
              </div>
            </el-form-item>
          </el-form>
        </div>
        <div
          class="preview-container"
          :class="{ disabled: isPreviewDisabled }"
          @mouseover="showTooltip = true"
          @mouseleave="showTooltip = false"
        >
          <span class="config-title">调试与预览</span>
          <div class="preview-area" :class="{ 'cursor-not-allowed': isPreviewDisabled }">
            <deep-chat
              id="chat-element"
              avatars="true"
              :text-input="{
                placeholder: { text: '请输入你的问题...' }
              }"
              :speech-to-text="{
                button: {
                  default: {
                    container: {
                      default: {
                        bottom: '1em',
                        right: '0.6em',
                        borderRadius: '20px',
                        width: '1.9em',
                        height: '1.9em'
                      }
                    },
                    svg: { styles: { default: { bottom: '0.35em', left: '0.35em' } } }
                  },
                  position: 'inside-right'
                }
              }"
              :mixed-files="{ button: { position: 'inside-left' } }"
              :demo="true"
              style="width: 100%; height: 100%; background-color: #ffffff; border: none"
            >
            </deep-chat>
          </div>
          <el-tooltip
            :content="tooltipContent"
            placement="top"
            :disabled="!isPreviewDisabled || !showTooltip"
            effect="light"
            popper-class="custom-tooltip"
          >
            <div v-if="isPreviewDisabled" class="overlay"></div>
          </el-tooltip>
        </div>
      </el-container>
    </el-container>
  </div>
</template>
<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import 'deep-chat'
import {
  ElForm,
  ElFormItem,
  ElInput,
  ElButton,
  ElContainer,
  ElHeader,
  ElSlider,
  ElSelect,
  ElOption,
  ElMessage
} from 'element-plus'
import { ArrowDown } from '@element-plus/icons-vue'
import uploadIcon from '../assets/material-symbols--upload-sharp.png'
import { Icon } from '@iconify/vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import type { DeepChat } from 'deep-chat'

import { Signals } from 'deep-chat/dist/types/handler'
import { ModelConfig, useConfigManagement } from './configManagement'

let chatElementRef: DeepChat | null = null
const capabilities = ref<Tool[]>([])
const avatarIcon = ref(uploadIcon)
const selectedCapabilities = ref([])
const temperatureValue = ref(1)
const agentForm = reactive({
  agent_name: '',
  agent_abstract: '',
  agent_info: '',
  max_tokens: 4096
})


const onUploadIcon = () => {
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = 'image/jpeg, image/png'
  input.onchange = (event) => {
    const file = (event.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        avatarIcon.value = e.target?.result as string
      }
      reader.readAsDataURL(file)
    }
  }
  input.click()
}

const configPlaceHolder =
  '' +
  '请详细描述你的工具设定,例如:\n' +
  '    工具特点,说明ta的能力、希望ta完成的工作或目标,ta的作用\n' +
  '    工具身份,描述ta的角色、和用户交互形式,需要规避的异常行为\n' +
  '    工具行为,指定ta的行为特点、性格或个性化回复用户的方式\n'
const router = useRouter() // 获取router实例
const goBack = () => {
  router.push('/')
}

onMounted(() => {
  getAvailableTools()

  const chatElement = document.querySelector('#chat-element')
  if (chatElement?.shadowRoot) {
    const observer = new MutationObserver((_, obs) => {
      const intropanel = chatElement.shadowRoot?.querySelector(
        '#messages > div.intro-panel'
      ) as HTMLElement | null
      if (intropanel) {
        intropanel.style.display = 'flex'
        obs.disconnect() // 停止观察
      }
    })

    observer.observe(chatElement.shadowRoot, {
      childList: true, // 观察直接子节点的添加或删除
      subtree: true, // 观察所有后代节点
      attributes: false, // 不观察属性变化
      characterData: false // 不观察文本内容变化
    })

    // 清理函数
    onUnmounted(() => {
      observer.disconnect()
    })
  }
})

const createTool = () => {
  // 创建工具的逻辑
}

const getAvailableTools = async () => {
  try {
    const response = await axios.get('http://127.0.0.1:7861/api/tools/available_tools', {
      headers: {
        accept: 'application/json'
      }
    })
    console.log(response.data)
    const tools = response.data.tools
    capabilities.value = tools.map((tool: string) => ({ label: tool, value: tool }))
  } catch (error) {
    console.error('Error fetching available tools:', error)
  }
}

const deleteConfig = async () => {
  try {
    const delete_agent_id = Number.parseInt(agentId.value as string, 10)
    const response = await axios.delete('http://127.0.0.1:7861/api/agent/delete_agent', {
      headers: {
        accept: 'application/json',
        'Content-Type': 'application/json'
      },
      data: delete_agent_id
    })
    console.log(response)
    ElMessage.success({
      message: '成功删除Agent配置',
      type: 'success'
    })
    // 处理成功响应
  } catch (error) {
    console.error('Error deleting agent:', error)
    ElMessage.error('删除配置失败')
  }
}

//监视agentForm.agent_name 如果有变化，就更新introMessage
watch(
  () => agentForm.agent_name,
  (newValue, oldValue) => {
    if (newValue !== oldValue) {
      if (chatElementRef) {
        chatElementRef.introMessage = { text: `你好！我是${newValue}，有什么事情需要我帮忙吗？` }
      }
    }
  }
)

/*********************************** deep-chat 对话配置 ***********************************/

function watchAndUpdateConfig() {
  watch(
    [selectedCapabilities, temperatureValue, agentForm],
    ([newCapabilities, newTemperature, newAgentForm]) => {
      // 更新 debugConversationConfig
      debugConversationConfig.agent_config = {
        ...debugConversationConfig.agent_config,
        tool_config: newCapabilities,
        temperature: newTemperature,
        agent_name: newAgentForm.agent_name,
        agent_abstract: newAgentForm.agent_abstract,
        agent_info: newAgentForm.agent_info,
        max_tokens: newAgentForm.max_tokens,
        agent_enable: true
      }
      console.log('更新：', newCapabilities, newTemperature, newAgentForm)
    },
    { deep: true } // 使用深度监视以捕获 agentForm 内部的变化
  )
}

onMounted(() => {
  chatElementRef = document.getElementById('chat-element') as DeepChat
  chatElementRef.introMessage = {
    text: `你好！我是${agentForm.agent_name}，有什么事情需要我帮忙吗？`
  }
  chatElementRef.connect = {
    handler: async (body, signals: Signals) => {
      handleDebugConversation(body, signals, chatElementRef as DeepChat)
    }
  }
  watchAndUpdateConfig()
})

/******************************************************************************/

import { useConversation } from './conversationApi'
import { Tool } from './toolConfig'

const { handleDebugConversation, debugConversationConfig } = useConversation()

const chatHistory = reactive([
  {
    content: `${agentForm.agent_abstract}`,
    role: 'user'
  },
  {
    content: `${agentForm.agent_info}`,
    role: 'user'
  }
]) // 初始化 chatHistory

watch(
  () => [agentForm.agent_abstract, agentForm.agent_info],
  ([newAbstract, newInfo], [oldAbstract, oldInfo]) => {
    if (newAbstract !== oldAbstract) {
      chatHistory[0].content = newAbstract
    }
    if (newInfo !== oldInfo) {
      chatHistory[1].content = newInfo
    }
    if (chatElementRef) {
      chatElementRef.clearMessages()
    }
  }
)

/*********************************** 对话配置 ***********************************/

const {
  configs,

  fetchAllConfigs
} = useConfigManagement()

const debugConfigSettings = ref({
  config_id: '',
  config_name: ''
})

const selectDebugModel = (config: ModelConfig) => {
  if (config) {
    debugConfigSettings.value.config_id = config.config_id as string
    debugConfigSettings.value.config_name = config.config_name
    debugConversationConfig.config_id = Number.parseInt(config.config_id as string, 10)
    console.log('debugConversationConfig.config_id:', debugConversationConfig.config_id)
  }
}

onMounted(async () => {
  await fetchAllConfigs()
})

/******************************************************************************/

/*********************************** 对话设置 ***********************************/

/******************************************************************************/

//从对话界面跳转到配置界面修改的处理逻辑
const route = useRoute()
const agentId = ref<string>('')

onMounted(async () => {
  agentId.value = route.query.agentId as string
  if (agentId.value) {
    await fetchAgentInfo(agentId.value)
  }
})

const fetchAgentInfo = async (id) => {
  try {
    const response = await axios.get(`http://127.0.0.1:7861/api/agent/get_agent?agent_id=${id}`)
    console.log(response)
    if (response.data.code === 200) {
      const agentData = response.data.data
      // 将获取的数据填充到表单中
      agentForm.agent_name = agentData.agent_name
      agentForm.agent_abstract = agentData.agent_abstract
      agentForm.agent_info = agentData.agent_info
      temperatureValue.value = agentData.temperature
      agentForm.max_tokens = agentData.max_tokens
      selectedCapabilities.value = agentData.tool_config
      avatarIcon.value = agentData.avatar || uploadIcon
      // 其他字段同理...
    }
  } catch (error) {
    console.error('Error fetching agent info:', error)
    ElMessage.error('获取Agent信息失败')
  }
}

const saveConfig = async () => {
  try {
    const avatarToUpload = avatarIcon.value === uploadIcon ? '' : avatarIcon.value
    const url = agentId.value
      ? 'http://127.0.0.1:7861/api/agent/update_agent'
      : 'http://127.0.0.1:7861/api/agent/create_agent'
    const method = agentId.value ? 'put' : 'post'

    const data = {
      agent_id: agentId.value,
      agent_name: agentForm.agent_name,
      agent_abstract: agentForm.agent_abstract,
      agent_info: agentForm.agent_info,
      temperature: temperatureValue.value,
      max_tokens: agentForm.max_tokens,
      tool_config: selectedCapabilities.value,
      avatar: avatarToUpload
    }

    const response = await axios[method](url, data, {
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.data.code === 200) {
      ElMessage.success({
        message: agentId.value ? '成功更新Agent配置' : '成功保存Agent配置',
        type: 'success'
      })
      router.push('/') // 保存后返回主页面
    } else {
      ElMessage.error({
        message: response.data.msg,
        type: 'error'
      })
    }
  } catch (error) {
    console.error('Error saving agent config:', error)
    ElMessage.error('保存配置失败')
  }
}

/*********************************** 监视聊天框是否可用 ***********************************/

const showTooltip = ref(false)

const isPreviewDisabled = computed(() => {
  return !agentForm.agent_name || !debugConfigSettings.value.config_name
})

const tooltipContent = computed(() => {
  if (!agentForm.agent_name && !debugConfigSettings.value.config_name) {
    return '请设置 Agent 名称并选择配置'
  } else if (!agentForm.agent_name) {
    return '请设置 Agent 名称'
  } else if (!debugConfigSettings.value.config_name) {
    return '请选择配置'
  }
  return ''
})

/******************************************************************************/
</script>

<style scoped>
.agent-avatar:hover {
  cursor: pointer;
}

.custom-tooltip {
  font-size: 16px !important; /* 增大字体大小 */
  padding: 10px 12px !important; /* 增加内边距 */
}

:deep(.intro-panel) {
  display: block;
}

.config-button {
  font-size: 16px;
  padding: 10px 20px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.left-icons {
  display: flex;
  align-items: center;
}

.back-button {
  margin-right: 10px;
  padding: 0;
}

.back-icon {
  width: 25px;
  height: 25px;
}

.content-container {
  flex: 1;
  overflow: hidden;
  display: flex;
}

.preview-container {
  position: relative;
  width: 50%;
  padding: 20px;
  display: flex;
  flex-direction: column;
  border: 1px solid #ddd;
  border-radius: 10px;
}

.preview-container.disabled .preview-area {
  opacity: 0.5;
  pointer-events: none;
}

.preview-area {
  flex: 1;
  background-color: #f9f9f9;
  overflow: hidden;
  display: flex;
  position: relative;
}

.cursor-not-allowed {
  cursor: not-allowed;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.5);
  z-index: 10;
  cursor: not-allowed;
}

.preview-area {
  flex: 1;
  background-color: #f9f9f9;
  overflow: hidden;
  display: flex;
}

deep-chat {
  flex: 1;
  width: 100%;
  height: 100%;
}

.config-title {
  font-size: 1.5em;
  font-weight: bold;
  padding-bottom: 20px;
}

.config-menu {
  padding: 20px;
  overflow-y: auto; /* Enable vertical scrolling */
  border: 1px solid #ddd; /* Add this line to add a border */
  border-radius: 10px; /* Optional: to add rounded corners */
}

.content-container {
  flex: 1;
  overflow: hidden;
  display: flex; /* Add this to enable flex layout */
}

.full-height {
  height: 98vh;
  display: flex;
  flex-direction: column;
}

.config-tips {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
  margin-top: 5px;
  margin-bottom: 5px;
  display: block;
}

.config-form {
  font-weight: bold;
  font-size: 1.2em;
}

.horizontal-menu {
  font-weight: bold;
}
</style>

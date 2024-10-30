<template>
  <div class="env-check">
    <h2>环境检查</h2>
    <el-steps :active="activeStep" finish-status="success">
      <el-step title="检查后端"></el-step>
      <el-step title="下载后端"></el-step>
      <el-step title="启动后端"></el-step>
    </el-steps>

    <div class="status">{{ status }}</div>

    <div v-if="showDownloadPrompt" class="download-prompt">
      <p>未检测到后端程序，是否下载？</p>
      <el-form :model="downloadForm" label-width="120px">
        <el-form-item label="下载路径">
          <el-input v-model="downloadForm.path">
            <template #append>
              <el-button @click="handleSelectPath">选择路径</el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>
      <div class="button-group">
        <el-button type="primary" @click="handleDownload" :loading="downloading">
          {{ downloading ? '下载中...' : '下载' }}
        </el-button>
        <el-button @click="handleExit">退出</el-button>
      </div>
    </div>

    <div v-if="error" class="error">
      <el-alert :title="error" type="error" :closable="false" show-icon />
      <div class="retry-options">
        <el-button type="primary" @click="handleRetry">重试</el-button>
        <el-button @click="handleRedownload">重新下载</el-button>
      </div>
    </div>

    <el-progress
      v-if="downloading"
      :percentage="downloadProgress"
      :format="progressFormat"
      style="margin-top: 20px"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import type { DownloadProgress } from '../../preload/index'

interface DownloadForm {
  path: string
}

const activeStep = ref(0)
const status = ref('正在检查后端...')
const showDownloadPrompt = ref(false)
const downloading = ref(false)
const downloadProgress = ref(0)
const error = ref('')

const downloadForm = ref<DownloadForm>({
  path: ''
})

onMounted(async () => {
  try {
    downloadForm.value.path = await window.api.getDefaultDownloadPath()
    const backendExists = await window.api.checkBackend()
    if (backendExists) {
      activeStep.value = 3
      window.api.completeEnvCheck(true)
    } else {
      showDownloadPrompt.value = true
    }
  } catch (err) {
    handleError(err as Error)
  }
})

const handleSelectPath = async () => {
  try {
    const result = await window.api.selectDirectory()
    if (result) {
      downloadForm.value.path = result
    }
  } catch (err) {
    handleError(err as Error)
  }
}

const handleDownload = async () => {
  if (!downloadForm.value.path) {
    ElMessage.error('请选择下载路径')
    return
  }

  downloading.value = true
  activeStep.value = 1
  status.value = '正在下载后端...'
  error.value = ''

  try {
    const success = await window.api.downloadBackend(
      downloadForm.value.path,
      (progress: DownloadProgress) => {
        downloadProgress.value = progress
      }
    )

    if (success) {
      await startBackend()
    } else {
      error.value = '下载失败，请检查网络连接后重试'
    }
  } catch (err) {
    handleError(err as Error)
  } finally {
    downloading.value = false
  }
}

const startBackend = async () => {
  activeStep.value = 2
  status.value = '正在启动后端...'
  error.value = ''

  try {
    const success = await window.api.startBackend()
    if (success) {
      ElMessage.success('环境检查完成')
      window.api.completeEnvCheck(true)
    } else {
      error.value = '后端启动失败，请检查是否有其他程序占用端口'
    }
  } catch (err) {
    handleError(err as Error)
  }
}

const handleRetry = () => {
  error.value = ''
  startBackend()
}

const handleRedownload = () => {
  error.value = ''
  showDownloadPrompt.value = true
  downloading.value = false
  downloadProgress.value = 0
}

const handleExit = () => {
  window.api.completeEnvCheck(false)
}

const handleError = (err: Error) => {
  error.value = `操作失败: ${err.message || '未知错误'}`
  console.error('Operation failed:', err)
}

const progressFormat = (percentage: number) => {
  return percentage === 100 ? '下载完成' : `${percentage}%`
}
</script>

<style scoped>
.env-check {
  padding: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.status {
  margin: 20px 0;
  text-align: center;
  font-size: 16px;
}

.download-prompt {
  text-align: center;
  margin: 20px 0;
}

.button-group {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.error {
  margin-top: 20px;
}

.retry-options {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  gap: 10px;
}
</style>

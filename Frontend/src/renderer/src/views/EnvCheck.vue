<template>
  <div class="env-check">
    <h2>环境检查</h2>
    <el-steps :active="activeStep" finish-status="success">
      <el-step title="检查Python环境"></el-step>
      <el-step title="检查必要库"></el-step>
      <el-step title="检查后端配置"></el-step>
    </el-steps>
    <div class="status">{{ status }}</div>
    <div class="button-group">
      <el-button @click="startCheck" :disabled="checkInProgress">开始检查</el-button>
      <el-button @click="skipCheck" type="warning">跳过检查</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeStep = ref(0)
const status = ref('点击开始检查环境')
const checkInProgress = ref(false)

const startCheck = async () => {
  checkInProgress.value = true
  status.value = '正在检查Python环境...'
  activeStep.value = 1

  try {
    // 这里应该实现实际的环境检查逻辑
    await checkPythonEnvironment()
    await checkRequiredLibraries()
    await checkBackendConfig()

    status.value = '环境检查完成'
    ElMessage.success('环境检查通过')
    window.electron.ipcRenderer.send('env-check-complete', true)
  } catch (error) {
    status.value = `检查失败: ${error.message}`
    ElMessage.error('环境检查失败')
    window.electron.ipcRenderer.send('env-check-complete', false)
  } finally {
    checkInProgress.value = false
  }
}

const skipCheck = () => {
  ElMessageBox.confirm(
    '跳过环境检查可能导致应用无法正常运行。是否确定跳过？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      ElMessage.warning('已跳过环境检查')
      window.electron.ipcRenderer.send('env-check-complete', true)
    })
    .catch(() => {
      ElMessage.info('已取消跳过')
    })
}

const checkPythonEnvironment = async () => {
  // 模拟Python环境检查
  await new Promise(resolve => setTimeout(resolve, 1000))
  activeStep.value = 2
}

const checkRequiredLibraries = async () => {
  // 模拟必要库检查
  await new Promise(resolve => setTimeout(resolve, 1000))
  activeStep.value = 3
}

const checkBackendConfig = async () => {
  // 模拟后端配置检查
  await new Promise(resolve => setTimeout(resolve, 1000))
}
</script>

<style scoped>
.env-check {
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status {
  margin: 20px 0;
}

.button-group {
  display: flex;
  gap: 10px;
}
</style>

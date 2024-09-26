<template>
  <el-card shadow="hover" class="file-card">
    <el-row :gutter="20" align="middle" justify="space-between">
      <el-col :span="20">
        <div class="d-flex align-items-center">
          <div class="file-icon mr-2">
            <Icon :icon="fileIcon" :width="24" :height="24" />
          </div>
          <el-tooltip :content="fileName" placement="top" :show-after="1000">
            <span class="file-name">{{ fileName }}</span>
          </el-tooltip>
        </div>
      </el-col>
      <el-col :span="4" class="text-right">
        <el-popconfirm
          title="确定要删除这个文件吗？"
          confirm-button-text="确定"
          cancel-button-text="取消"
          @confirm="handleDelete"
        >
          <template #reference>
            <el-button type="danger" :icon="Delete" circle size="small" />
          </template>
        </el-popconfirm>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { Icon } from '@iconify/vue'

defineOptions({
  name: 'ReFileCard'
})

interface Props {
  fileName: string
  lastUpdated: string
  knowledgeBaseName: string
}

const props = defineProps<Props>()
const emit = defineEmits(['delete'])

const fileExtension = computed(() => {
  const parts = props.fileName.split('.')
  return parts.length > 1 ? parts.pop()!.toLowerCase() : ''
})

const fileIcon = computed(() => {
  switch (fileExtension.value) {
    case 'md':
      return 'vscode-icons:file-type-markdown'
    case 'js':
      return 'vscode-icons:file-type-js'
    case 'ts':
      return 'vscode-icons:file-type-typescript'
    case 'html':
      return 'vscode-icons:file-type-html'
    case 'css':
      return 'vscode-icons:file-type-css'
    case 'json':
      return 'vscode-icons:file-type-json'
    case 'py':
      return 'vscode-icons:file-type-python'
    case 'jpg':
    case 'jpeg':
    case 'png':
    case 'gif':
      return 'vscode-icons:file-type-image'
    case 'pdf':
      return 'vscode-icons:file-type-pdf'
    // 添加更多文件类型...
    default:
      return 'vscode-icons:default-file'
  }
})

const handleDelete = () => {
  emit('delete', props.knowledgeBaseName, props.fileName)
}
</script>

<style scoped>
.file-card {
  margin-bottom: 10px;
}

.file-name {
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
  display: inline-block;
  vertical-align: middle;
}

.d-flex {
  display: flex;
}

.align-items-center {
  align-items: center;
}

.mr-2 {
  margin-right: 15px;
}

.text-right {
  text-align: right;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>

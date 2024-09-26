<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`${kbName} 的文件列表`"
    width="80%"
    :fullscreen="false"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    custom-class="fixed-size-dialog"
  >
    <div class="dialog-header">
      <div class="left-side">
        <el-button @click="handleNewFile">
          <Icon icon="material-symbols:add" />
          &nbsp; 新建文件
        </el-button>
      </div>
      <div class="right-side">
        <el-input v-model="searchValue" style="width: 300px" placeholder="请输入文件名称" clearable>
          <template #suffix>
            <Icon v-show="searchValue.length === 0" icon="ri:search-line" />
          </template>
        </el-input>
      </div>
    </div>

    <div class="file-list-container" @dragover.prevent @drop.prevent="handleDrop">
      <el-scrollbar height="500px">
        <el-row :gutter="16">
          <el-col
            v-for="doc in filteredDocuments"
            :key="doc.file_name"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            :xl="4"
          >
            <ReFileCard
              :file-name="doc.file_name"
              :last-updated="doc.create_time"
              :knowledge-base-name="kbName"
              @delete="handleDeleteFile"
            />
          </el-col>
        </el-row>
      </el-scrollbar>
    </div>

    <!-- 新建文件对话框 -->
    <el-dialog
      v-model="newFileDialogVisible"
      title="新建文件"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <el-form :model="uploadOptions" label-width="150px">
        <el-form-item label="覆盖已有文件">
          <el-switch v-model="uploadOptions.override" />
        </el-form-item>
        <el-form-item label="上传后向量化">
          <el-switch v-model="uploadOptions.to_vector_store" />
        </el-form-item>
        <el-form-item label="单段文本最大长度">
          <el-input-number v-model="uploadOptions.chunk_size" :min="1" />
        </el-form-item>
        <el-form-item label="相邻文本重合长度">
          <el-input-number v-model="uploadOptions.chunk_overlap" :min="0" />
        </el-form-item>
        <el-form-item label="中文标题加强">
          <el-switch v-model="uploadOptions.zh_title_enhance" />
        </el-form-item>
        <el-form-item label="暂不保存向量库">
          <el-switch v-model="uploadOptions.not_refresh_vs_cache" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
            class="file-upload"
            :auto-upload="false"
            :on-change="handleNewFileChange"
            :file-list="newFileUpload"
            multiple
          >
            <el-button type="primary">选择文件</el-button>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="newFileDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUploadNewFile">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="dialogVisible = false">关闭</el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import ReFileCard from '../../components/fileCard.vue'
import { useKnowledgeBase } from './kbapi'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'

defineOptions({
  name: 'FileListDialog'
})

const searchValue = ref('')
const newFileUpload = ref<[]>([])
const newFileDialogVisible = ref(false)
const uploadOptions = reactive({
  override: false,
  to_vector_store: true,
  chunk_size: 250,
  chunk_overlap: 50,
  zh_title_enhance: false,
  not_refresh_vs_cache: false
})

const filteredDocuments = computed(() => {
  return props.documents.filter((doc) =>
    doc.file_name.toLowerCase().includes(searchValue.value.toLowerCase())
  )
})

const handleNewFileChange = (file: File, fileList: File[]) => {
  newFileUpload.value = fileList.map((file) => file.raw) as []
}

interface Props {
  visible: boolean
  kbName: string
  documents: {
    kb_name: string
    file_name: string
    file_ext: string
    file_version: number
    document_loader: string
    docs_count: number
    text_splitter: string
    create_time: string
    in_folder: boolean
    in_db: boolean
    file_mtime: number
    file_size: number
    custom_docs: boolean
    No: number
  }[]
}

const props = defineProps<Props>()
const emit = defineEmits(['update:visible', 'refresh-documents'])

const dialogVisible = ref(props.visible)
const { deleteDocument, fetchDocuments, uploadDocument } = useKnowledgeBase()

watch(
  () => props.visible,
  (newValue) => {
    dialogVisible.value = newValue
  }
)

watch(dialogVisible, (newValue) => {
  emit('update:visible', newValue)
})

const handleNewFile = () => {
  newFileDialogVisible.value = true
}
const handleUploadNewFile = async () => {
  const files = newFileUpload.value
  if (files.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  const success = await uploadDocument(files, props.kbName, uploadOptions)

  if (success) {
    newFileDialogVisible.value = false
    await refreshDocuments()
  }
  // Clear the file list after upload attempt
  newFileUpload.value = []
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    for (let i = 0; i < files.length; i++) {
      try {
        const success = await uploadDocument([files[i]], props.kbName)
        if (success) {
          ElMessage.success(`文件 ${files[i].name} 上传成功`)
        }
      } catch (error) {
        if (error instanceof Error) {
          ElMessage.error(`文件 ${files[i].name} 上传失败: ${error.message}`)
        } else {
          ElMessage.error(`文件 ${files[i].name} 上传失败: 未知错误`)
        }
      }
    }
    await refreshDocuments()
  }
}

const handleDeleteFile = async (knowledgeBaseName: string, fileName: string) => {
  try {
    await deleteDocument(knowledgeBaseName, fileName)
    await refreshDocuments()
  } catch (error) {
    console.error('删除文件失败:', error)
  }
}

const refreshDocuments = async () => {
  await fetchDocuments(props.kbName)
  emit('refresh-documents')
}
</script>

<style scoped>
.fixed-size-dialog {
  display: flex;
  flex-direction: column;
  height: 90vh;
  max-height: 800px;
}

.fixed-size-dialog :deep(.el-dialog__body) {
  flex: 1;
  overflow: hidden;
  padding: 10px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.left-side {
  display: flex;
  align-items: center;
}

.right-side {
  display: flex;
  align-items: center;
}

.file-list-container {
  height: 100%;
}

.el-row {
  margin-bottom: -16px;
  margin-right: -8px;
  margin-left: -8px;
}

.el-col {
  padding-bottom: 16px;
  padding-right: 8px;
  padding-left: 8px;
}

.file-upload {
  display: inline-block;
}

.file-upload .el-upload {
  width: auto;
}

.file-upload .el-upload-dragger {
  width: auto;
  height: auto;
  border: none;
  border-radius: 0;
}

.file-upload .el-upload-dragger:hover {
  border: none;
}

.file-upload .el-button {
  margin-right: 10px;
}
</style>

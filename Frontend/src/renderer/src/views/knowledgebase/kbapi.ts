import axios from 'axios'
import { ref, reactive, computed } from 'vue'
import { ElLoading, ElMessage } from 'element-plus'

export const KB_API_BASE_URL = 'http://127.0.0.1:7861/knowledge_base'

export interface KnowledgeBase {
  id: number
  kb_name: string
  kb_info: string
  vs_type: string
  embed_model: string
  file_count: number
  create_time: string
}

export interface Document {
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
}

export interface UploadDocumentOptions {
  override?: boolean
  to_vector_store?: boolean
  chunk_size?: number
  chunk_overlap?: number
  zh_title_enhance?: boolean
  not_refresh_vs_cache?: boolean
}

export const useKnowledgeBase = () => {
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const activeKnowledgeBase = ref('')
  const isShowKnowledgeBaseDialog = ref(false)
  const knowledgeBaseForm = reactive({
    knowledge_base_name: '',
    vector_store_type: 'faiss',
    kb_info: ''
  })
  // 文档列表
  const documents = ref<Document[]>([])

  const isSaveButtonDisabled = computed(() => !knowledgeBaseForm.knowledge_base_name?.trim())

  const fetchAllKnowledgeBases = async () => {
    try {
      const response = await axios.get(`${KB_API_BASE_URL}/list_knowledge_bases`)
      if (response.data.code === 200) {
        knowledgeBases.value = response.data.data
      } else {
        ElMessage.error(response.data.msg || '获取知识库列表失败')
      }
    } catch (error) {
      ElMessage.error('无法获取知识库列表')
      console.error('Failed to fetch knowledge bases:', error)
    }
  }

  const createKnowledgeBase = async () => {
    try {
      const response = await axios.post(
        `${KB_API_BASE_URL}/create_knowledge_base`,
        knowledgeBaseForm
      )
      if (response.data.code === 200) {
        ElMessage.success('知识库创建成功')
        await fetchAllKnowledgeBases()
        return response.data.data
      } else {
        ElMessage.error(response.data.msg)
      }
    } catch (error) {
      ElMessage.error('创建知识库失败')
      console.error('Failed to create knowledge base:', error)
    }
    return null
  }
  const deleteKnowledgeBase = async (kbName: string) => {
    try {
      const response = await axios.post(`${KB_API_BASE_URL}/delete_knowledge_base`, kbName)
      if (response.data.code === 200) {
        ElMessage.success('知识库删除成功')
        await fetchAllKnowledgeBases()
        activeKnowledgeBase.value = ''
      } else {
        ElMessage.error(response.data.msg || '删除知识库失败')
      }
    } catch (error) {
      ElMessage.error('删除知识库失败')
      console.error('Failed to delete knowledge base:', error)
    }
  }
  const fetchDocuments = async (kbName: string) => {
    try {
      const response = await axios.get(`${KB_API_BASE_URL}/list_files`, {
        params: { knowledge_base_name: kbName }
      })
      if (response.data.code === 200) {
        documents.value = response.data.data
        console.log('documents.value:', documents.value)
      } else {
        ElMessage.error(response.data.msg)
      }
    } catch (error) {
      ElMessage.error('无法获取文档列表')
      console.error('Failed to fetch documents:', error)
    }
  }

  const uploadDocument = async (
    file: File | File[],
    kbName: string,
    options: UploadDocumentOptions = {}
  ) => {
    const formData = new FormData()

    // 处理单个文件或多个文件
    if (Array.isArray(file)) {
      file.forEach((f) => formData.append('files', f))
    } else {
      formData.append('files', file)
    }

    formData.append('knowledge_base_name', kbName)

    // 添加可选参数
    if (options.override !== undefined) formData.append('override', options.override.toString())
    if (options.to_vector_store !== undefined)
      formData.append('to_vector_store', options.to_vector_store.toString())
    if (options.chunk_size !== undefined)
      formData.append('chunk_size', Math.floor(options.chunk_size).toString())
    if (options.chunk_overlap !== undefined)
      formData.append('chunk_overlap', Math.floor(options.chunk_overlap).toString())
    if (options.zh_title_enhance !== undefined)
      formData.append('zh_title_enhance', options.zh_title_enhance.toString())
    if (options.not_refresh_vs_cache !== undefined)
      formData.append('not_refresh_vs_cache', options.not_refresh_vs_cache.toString())

    // 显示加载动画
    const loadingInstance = ElLoading.service({
      lock: true,
      text: '文件上传中...',
      background: 'rgba(0, 0, 0, 0.7)'
    })

    try {
      const response = await axios.post(`${KB_API_BASE_URL}/upload_docs`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      if (response.data.code === 200) {
        ElMessage.success('文档上传成功')
        // 假设 fetchDocuments 是一个更新文档列表的函数
        await fetchDocuments(kbName)
        return true
      } else {
        ElMessage.error(response.data.msg || '上传文档失败')
        return false
      }
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        // 处理 Axios 错误
        const errorMessage =
          error.response.data?.detail || error.response.data?.msg || '上传文档失败'
        ElMessage.error(errorMessage)
        console.error('Failed to upload document:', error.response.data)
      } else {
        // 处理非 Axios 错误
        ElMessage.error('上传文档时发生未知错误')
        console.error('Failed to upload document:', error)
      }
      return false
    } finally {
      // 关闭加载动画
      loadingInstance.close()
    }
  }

  const deleteDocument = async (kbName: string, fileName: string) => {
    try {
      const response = await axios.post(`${KB_API_BASE_URL}/delete_docs`, {
        knowledge_base_name: kbName,
        file_names: [fileName],
        delete_content: true,
        not_refresh_vs_cache: false
      })
      if (response.data.code === 200) {
        ElMessage.success('文档删除成功')
        await fetchDocuments(kbName)
      } else {
        ElMessage.error(response.data.msg)
      }
    } catch (error) {
      ElMessage.error('删除文档失败')
      console.error('Failed to delete document:', error)
    }
  }

  const updateKnowledgeBaseInfo = async (kbName: string, kbInfo: string) => {
    try {
      const response = await axios.post(`${KB_API_BASE_URL}/update_info`, {
        kb_name: kbName,
        kb_info: kbInfo
      })
      if (response.data.code === 200) {
        ElMessage.success('知识库信息更新成功')
        await fetchAllKnowledgeBases()
      } else {
        ElMessage.error(response.data.msg)
      }
    } catch (error) {
      ElMessage.error('更新知识库信息失败')
      console.error('Failed to update knowledge base info:', error)
    }
  }

  const handleNewKnowledgeBase = () => {
    activeKnowledgeBase.value = ''
    Object.assign(knowledgeBaseForm, {
      kb_name: '',
      vs_type: 'faiss',
      kb_info: ''
    })
  }

  const handleSaveKnowledgeBase = async () => {
    if (activeKnowledgeBase.value) {
      await updateKnowledgeBaseInfo(activeKnowledgeBase.value, knowledgeBaseForm.kb_info || '')
    } else {
      const newKnowledgeBase = await createKnowledgeBase()
      if (newKnowledgeBase) {
        activeKnowledgeBase.value = newKnowledgeBase.kb_name
      }
    }
  }

  const handleDeleteKnowledgeBase = async (kbName: string) => {
    if (kbName) {
      await deleteKnowledgeBase(kbName)
    } else {
      ElMessage.warning('请选择要删除的知识库')
    }
  }

  const handleKnowledgeBaseSelect = async (kbName: string) => {
    activeKnowledgeBase.value = kbName
    await fetchDocuments(kbName)
  }

  return {
    knowledgeBases,
    activeKnowledgeBase,
    isShowKnowledgeBaseDialog,
    knowledgeBaseForm,
    documents,
    isSaveButtonDisabled,
    fetchAllKnowledgeBases,
    handleNewKnowledgeBase,
    handleSaveKnowledgeBase,
    handleDeleteKnowledgeBase,
    handleKnowledgeBaseSelect,
    uploadDocument,
    deleteDocument,
    deleteKnowledgeBase,
    updateKnowledgeBaseInfo,
    fetchDocuments
  }
}

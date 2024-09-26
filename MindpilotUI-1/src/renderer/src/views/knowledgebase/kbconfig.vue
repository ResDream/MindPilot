<template>
  <div class="kb-layout">
    <el-container>
      <el-header class="flex items-center">
        <Icon icon="weui:back-filled" @click="goBack" class="cursor-pointer mr-2" />
        <h1>知识中心</h1>
      </el-header>
      <el-main>
        <div class="w-full flex justify-between mb-4">
          <el-button @click="handleNewKnowledgeBaseClick">
            <Icon icon="material-symbols:add" />
            &nbsp; 新建知识库
          </el-button>

          <el-input
            v-model="searchValue"
            style="width: 300px"
            placeholder="请输入知识库名称"
            clearable
          >
            <template #suffix>
              <Icon v-show="searchValue.length === 0" icon="ri:search-line" />
            </template>
          </el-input>
        </div>
        <div v-loading="dataLoading">
          <el-empty
            v-show="displayedKnowledgeBases.length === 0"
            :description="`${searchValue} 知识库不存在`"
          />
          <template v-if="pagination.total > 0">
            <el-row :gutter="16">
              <el-col
                v-for="kb in displayedKnowledgeBases"
                :key="kb.kb_name"
                :xs="24"
                :sm="12"
                :md="8"
                :lg="6"
                :xl="4"
              >
                <ReCard
                  :product="mapKnowledgeBaseToProduct(kb)"
                  @delete-item="handleDeleteItem"
                  @manage-product="handleManageProduct"
                />
              </el-col>
            </el-row>
          </template>
        </div>
      </el-main>
      <el-footer>
        <el-pagination
          v-model:currentPage="pagination.current"
          class="float-right mt-4"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[12, 24, 36]"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="onPageSizeChange"
          @current-change="onCurrentChange"
        />
      </el-footer>
    </el-container>
    <ListDialogForm v-model:visible="isShowKnowledgeBaseDialog" :data="knowledgeBaseForm" />
    <FileListDialog
      v-model:visible="isShowFileListDialog"
      :kb-name="activeKnowledgeBase"
      :documents="documents"
      @refresh-documents="handleRefreshDocuments"
    />
    <NewKBDialog
      v-model:visible="isShowKnowledgeBaseDialog"
      :loading="loading"
      :form="knowledgeBaseForm"
      @save="handleSaveKnowledgeBaseClick"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ReCard from '../../components/ListCard.vue'
import { Icon } from '@iconify/vue'
import { useKnowledgeBase } from './kbapi'
import FileListDialog from './filelistdialog.vue'
import NewKBDialog from './newkbdialog.vue'
import { router } from '../../router'

const {
  knowledgeBases,
  activeKnowledgeBase,
  isShowKnowledgeBaseDialog,
  knowledgeBaseForm,
  documents,
  fetchAllKnowledgeBases,
  handleNewKnowledgeBase,
  handleSaveKnowledgeBase,
  handleDeleteKnowledgeBase,
  fetchDocuments
} = useKnowledgeBase()

const pagination = ref({ current: 1, pageSize: 12, total: 0 })
const dataLoading = ref(true)
const loading = ref(false)
const searchValue = ref('')
const isShowFileListDialog = ref(false)

const displayedKnowledgeBases = computed(() => {
  const start = (pagination.value.current - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return knowledgeBases.value
    .slice(start, end)
    .filter((kb) => kb.kb_name.toLowerCase().includes(searchValue.value.toLowerCase()))
})

const mapKnowledgeBaseToProduct = (kb) => ({
  name: kb.kb_name,
  isSetup: true,
  description: kb.kb_info,
  type: 1,
  fileCount: kb.file_count,
  lastUpdatedAt: kb.create_time
})

onMounted(async () => {
  dataLoading.value = true
  await fetchAllKnowledgeBases()
  pagination.value.total = knowledgeBases.value.length
  dataLoading.value = false
})

const onPageSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.current = 1
}

const onCurrentChange = (current: number) => {
  pagination.value.current = current
}

const handleDeleteItem = (product) => {
  ElMessageBox.confirm(
    product ? `确认删除后${product.name}的所有知识库信息将被清空, 且无法恢复` : '',
    '提示',
    {
      type: 'warning'
    }
  )
    .then(() => {
      handleDeleteKnowledgeBase(product.name)
      fetchAllKnowledgeBases()
    })
    .catch(() => {})
}

const handleManageProduct = (product) => {
  handleKnowledgeBaseClick(product.name)
}

const handleKnowledgeBaseClick = async (kbName: string) => {
  activeKnowledgeBase.value = kbName
  await fetchDocuments(kbName)
  isShowFileListDialog.value = true
}

const handleNewKnowledgeBaseClick = () => {
  handleNewKnowledgeBase() // Reset the form
  isShowKnowledgeBaseDialog.value = true // Show the dialog
}

const handleRefreshDocuments = async () => {
  await fetchDocuments(activeKnowledgeBase.value)
  await fetchAllKnowledgeBases()
}

const handleSaveKnowledgeBaseClick = async () => {
  loading.value = true // 启动 Loading
  try {
    await handleSaveKnowledgeBase()
    isShowKnowledgeBaseDialog.value = false
    await fetchAllKnowledgeBases()
    await nextTick()
  } catch (error) {
    ElMessage.error('创建知识库失败')
  } finally {
    loading.value = false // 关闭 Loading
  }
}

const goBack = () => {
  router.back()
}
</script>

<style lang="scss" scoped>
.icon-back {
  margin-right: 8px;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.cursor-pointer {
  cursor: pointer;
}

.mr-2 {
  margin-right: 0.5rem;
}

.kb-layout {
  //height: 100svh;
  display: flex;
  flex-direction: column;

  .el-container {
    height: 100%;
  }

  .el-header {
    background-color: #f5f7fa;
    color: #333;
  }

  .el-main {
    overflow-y: auto;
  }
}

.w-full {
  width: 100%;
}

.flex {
  display: flex;
}

.justify-between {
  justify-content: space-between;
}

.mb-4 {
  margin-bottom: 1rem;
}

.float-right {
  float: right;
}

.mt-4 {
  margin-top: 1rem;
}
</style>

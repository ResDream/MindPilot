<template>
  <el-dialog v-model="dialogVisible" title="新建知识库" width="30%" @close="handleClose">
    <div
      v-loading="loading"
      :element-loading-text="loadingText"
      element-loading-spinner="el-icon-loading"
    >
      <el-form :model="form" label-width="120px">
        <el-form-item label="知识库名称">
          <el-input
            v-model="
              // eslint-disable-next-line vue/no-mutating-props
              form.knowledge_base_name
            "
          />
        </el-form-item>
        <el-form-item label="向量库类型">
          <el-select
            v-model="
              // eslint-disable-next-line vue/no-mutating-props
              form.vector_store_type
            "
          >
            <el-option label="Faiss" value="faiss" />
            <!-- Add other options if needed -->
          </el-select>
        </el-form-item>
        <el-form-item label="知识库描述">
          <el-input
            v-model="
              // eslint-disable-next-line vue/no-mutating-props
              form.kb_info
            "
            type="textarea"
          />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">取消</el-button>
        <el-button type="primary" @click="handleSave" :disabled="isSaveDisabled || loading">
          确定
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

defineOptions({
  name: 'NewKBDialog'
})

const props = defineProps<{
  visible: boolean
  loading: boolean
  form: {
    knowledge_base_name: string
    vector_store_type: string
    kb_info: string
  }
}>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'save'): void
}>()

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const isSaveDisabled = computed(() => !props.form.knowledge_base_name.trim())

const loadingText = ref('创建知识库中...')

const handleClose = () => {
  if (!props.loading) {
    emit('update:visible', false)
  }
}

const handleSave = () => {
  emit('save')
}
</script>

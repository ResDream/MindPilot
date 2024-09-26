<template>
  <div :class="cardClass">
    <div class="list-card-item_detail bg-bg_color">
      <div class="list-card-item_header">
        <div class="list-card-item_detail--left">
          <div :class="cardLogoClass">
            <Icon icon="fluent-emoji:open-book"></Icon>
          </div>
          <p class="list-card-item_detail--name text-text_color_primary">
            {{ product.name }}
          </p>
        </div>
        <div class="list-card-item_detail--operation">
          <el-dropdown trigger="click" :disabled="!product.isSetup">
            <IconifyIconOffline :icon="More2Fill" class="text-[24px]" />
            <template #dropdown>
              <el-dropdown-menu :disabled="!product.isSetup">
                <el-dropdown-item @click="handleClickManage(product)"> 管理 </el-dropdown-item>
                <el-dropdown-item @click="handleClickDelete(product)"> 删除 </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <p class="list-card-item_detail--desc text-text_color_regular">
        {{ product.description }}
      </p>
      <el-row class="mt-4">
        <el-col :span="12">
          <el-statistic title="文件数量" :value="formattedFileCount" />
        </el-col>
        <el-col :span="12">
          <el-statistic title="最后更新时间" :value="formattedLastUpdatedAt" />
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, PropType } from 'vue'
import { Icon } from '@iconify/vue'
import More2Fill from '@iconify-icons/ri/more-2-fill'
import IconifyIconOffline from './ReIcon/src/iconifyIconOffline'

defineOptions({
  name: 'ReCard'
})

interface CardProductType {
  type: number
  isSetup: boolean
  description: string
  name: string
  fileCount: number
  lastUpdatedAt: Date | null
}

const props = defineProps({
  product: {
    type: Object as PropType<CardProductType>,
    required: true
  }
})

const emit = defineEmits(['manage-product', 'delete-item'])

const handleClickManage = (product: CardProductType) => {
  emit('manage-product', product)
}

const handleClickDelete = (product: CardProductType) => {
  emit('delete-item', product)
}

const cardClass = computed(() => [
  'list-card-item',
  { 'list-card-item__disabled': !props.product.isSetup }
])

const cardLogoClass = computed(() => [
  'list-card-item_detail--logo',
  { 'list-card-item_detail--logo__disabled': !props.product.isSetup }
])

const formattedFileCount = computed(() => props.product.fileCount ?? 0)

const formattedLastUpdatedAt = computed(() => {
  const date = new Date(props.product.lastUpdatedAt)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  })
})
</script>

<style scoped lang="scss">
.list-card-item {
  display: flex;
  flex-direction: column;
  margin-bottom: 12px;
  overflow: hidden;
  cursor: pointer;
  border-radius: 3px;

  &_detail {
    flex: 1;
    min-height: 140px;
    padding: 24px 32px;

    &--left {
      display: flex;
      align-items: center;
      flex: 1;
      min-width: 0;
      overflow: hidden;
    }

    &--logo {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 46px;
      height: 46px;
      font-size: 26px;
      color: #0052d9;
      background: #e0ebff;
      border-radius: 50%;
      margin-right: 16px;
      flex-shrink: 0;

      &__disabled {
        color: #a1c4ff;
      }
    }

    &--operation {
      display: flex;
      align-items: center;

      &--tag {
        border: 0;
        margin-right: 8px;
      }
    }

    &--name {
      margin: 0;
      font-size: 16px;
      font-weight: 400;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    &--desc {
      display: -webkit-box;
      height: 40px;
      margin-top: 14px;
      margin-bottom: 0;
      overflow: hidden;
      font-size: 14px;
      line-height: 20px;
      text-overflow: ellipsis;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }
  }

  &_header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  &__disabled {
    .list-card-item_detail--name,
    .list-card-item_detail--desc {
      color: var(--el-text-color-disabled);
    }

    .list-card-item_detail--operation--tag {
      color: #bababa;
    }
  }
}
</style>

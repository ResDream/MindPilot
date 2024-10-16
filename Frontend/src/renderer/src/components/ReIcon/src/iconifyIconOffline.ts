import { h, defineComponent, PropType } from 'vue'
import { Icon as IconifyIcon, addIcon } from '@iconify/vue/dist/offline'

// Iconify Icon在Vue里本地使用（用于内网环境）
export default defineComponent({
  name: 'IconifyIconOffline',
  components: { IconifyIcon },
  props: {
    icon: {
      type: [Object, null] as PropType<typeof IconifyIcon | null>,
      default: null
    }
  },
  render() {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-expect-error
    if (typeof this.icon === 'object') addIcon(this.icon, this.icon)
    const attrs = this.$attrs
    return h(
      IconifyIcon,
      {
        // eslint-disable-next-line @typescript-eslint/ban-ts-comment
        // @ts-expect-error
        icon: this.icon,
        style: attrs?.style ? Object.assign(attrs.style, { outline: 'none' }) : { outline: 'none' },
        ...attrs
      },
      {
        default: () => []
      }
    )
  }
})

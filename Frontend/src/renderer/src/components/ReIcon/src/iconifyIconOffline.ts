import { h, defineComponent, type PropType } from "vue"
import { Icon, type IconifyIcon } from "@iconify/vue/dist/offline"

export default defineComponent({
  name: "IconifyIconOffline",
  props: {
    icon: { type: Object as PropType<IconifyIcon>, required: true }
  },
  setup(props, { attrs }) {
    return () => h(Icon, { ...attrs, icon: props.icon })
  }
})

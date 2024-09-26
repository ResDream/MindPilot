import type { DeepChat } from 'deep-chat'

export function extractFirstJSON(text: string): any | null {
  const jsonRegex = /\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}/
  const match = text.match(jsonRegex)

  if (match) {
    try {
      return JSON.parse(match[0])
    } catch (error) {
      console.warn('Failed to parse JSON:', error)
    }
  }

  return null
}

export const clearMessageElement = (deepChatRef: DeepChat | null) => {
  if (!deepChatRef) {
    console.log('deepChatRef is not valid')
    return
  }
  // 获取所有 class="outer-message-container" 的元素
  const messagesElements = deepChatRef.shadowRoot!.querySelectorAll('.outer-message-container')
  console.log('messagesElements:', messagesElements)

  // 遍历并删除每个元素
  messagesElements.forEach((element) => {
    console.log('Removing element:', element)
    element.remove()
  })
}

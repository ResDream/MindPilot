import { createParser } from "eventsource-parser"

export interface ConversationEvent {
  type: "started" | "model_start" | "token" | "model_end" | "tool_start" | "tool_end" | "answer" | "done" | "error"
  run_id?: string
  text?: string
  name?: string
  input?: unknown
}

export async function readConversationStream(
  response: Response, onEvent: (event: ConversationEvent) => void
): Promise<void> {
  if (!response.ok) throw new Error(`请求失败：${response.status} ${await response.text()}`)
  if (!response.body) throw new Error("服务端没有返回事件流")
  let completed = false
  const parser = createParser({
    onEvent(message) {
      const event: ConversationEvent = JSON.parse(message.data)
      if (event.type === "error") throw new Error(event.text || "任务执行失败")
      if (event.type === "done") completed = true
      onEvent(event)
    },
    onError(error) { throw error }
  })
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      parser.feed(decoder.decode(value, { stream: true }))
    }
    parser.feed(decoder.decode())
    if (!completed) throw new Error("连接已中断，任务没有完成")
  } finally {
    await reader.cancel()
    reader.releaseLock()
  }
}

export const localModels = [
  "Qwen2.5-72B-Instruct", "Qwen2.5-32B-Instruct", "Qwen2.5-14B-Instruct",
  "Qwen2.5-7B-Instruct", "Qwen2.5-3B-Instruct", "Qwen2.5-1.5B-Instruct",
  "Qwen2.5-0.5B-Instruct", "Qwen2.5-Coder-32B-Instruct",
  "QwQ-32B-Preview", "MiniCPM-2B", "Qwen2-0.5B"
]

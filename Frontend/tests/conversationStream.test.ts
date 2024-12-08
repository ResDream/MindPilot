import { describe, expect, it } from "vitest"
import { readConversationStream, type ConversationEvent } from "../src/renderer/src/views/conversationStream"

describe("会话事件流", () => {
  it("处理跨网络分块的中文消息", async () => {
    const bytes = new TextEncoder().encode(
      `data: ${JSON.stringify({ type: "answer", text: "中文结果" })}\n\ndata: {"type":"done"}\n\n`
    )
    const stream = new ReadableStream({
      start(controller) {
        for (const byte of bytes) controller.enqueue(new Uint8Array([byte]))
        controller.close()
      }
    })
    const events: ConversationEvent[] = []
    await readConversationStream(new Response(stream), (event) => events.push(event))
    expect(events).toEqual([{ type: "answer", text: "中文结果" }, { type: "done" }])
  })

  it("报告缺失的结束事件", async () => {
    await expect(readConversationStream(new Response("data: {\"type\":\"started\"}\n\n"), () => {}))
      .rejects.toThrow("连接已中断")
  })

  it("传播服务端执行错误", async () => {
    const response = new Response(`data: ${JSON.stringify({ type: "error", text: "模型加载失败" })}\n\n`)
    await expect(readConversationStream(response, () => {})).rejects.toThrow("模型加载失败")
  })

  it("拒绝失败的 HTTP 响应", async () => {
    await expect(readConversationStream(new Response("配置不存在", { status: 404 }), () => {}))
      .rejects.toThrow("404")
  })
})

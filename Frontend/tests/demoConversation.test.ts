import { describe, expect, it } from "vitest"
import data from "../../docs/examples/qwen2.5-2024.json"
import { demoEvents, demoTask } from "../src/renderer/src/views/demoConversation"

describe("历史资料任务", () => {
  it("工具调用和结果逐一对应", () => {
    const pending = new Map<string, string>()
    const completed = new Set<string>()
    for (const event of demoEvents) {
      if (event.type === "tool_start") {
        expect(event.run_id).toBeTruthy()
        expect(event.name).toBeTruthy()
        const id = event.run_id!
        expect(pending.has(id) || completed.has(id)).toBe(false)
        pending.set(id, event.name!)
      } else if (event.type === "tool_end") {
        const id = event.run_id!
        expect(pending.get(id)).toBe(event.name)
        expect(event.text?.length).toBeGreaterThan(0)
        pending.delete(id)
        completed.add(id)
      } else if (event.type === "answer") {
        expect(pending.size).toBe(0)
      }
    }
    expect(completed.size).toBe(14)
    expect(demoEvents.at(-1)?.type).toBe("answer")
    expect(demoEvents.filter((event) => event.type === "answer")).toHaveLength(1)
  })

  it("计算器输入和返回值对应已保存的计算记录", () => {
    for (const calculation of data.calculations) {
      const start = demoEvents.find((event) => event.run_id === calculation.id && event.type === "tool_start")
      const end = demoEvents.find((event) => event.run_id === calculation.id && event.type === "tool_end")
      expect(start?.input).toEqual({ text: calculation.expression })
      expect(Number(end?.text)).toBe(calculation.value)
    }
  })

  it("显存与耗时计算使用真实参数", () => {
    const model = data.model
    const weights = model.parametersBillions * 1e9 * 2 / 1024 ** 3
    const kvToken = 2 * model.layers * model.kvHeads * (model.hiddenSize / model.queryHeads) * 2
    const kvRequest = kvToken * model.defaultContext / 1024 ** 3
    const expected = new Map([
      ["weights", weights], ["kv-token", kvToken], ["kv-request", kvRequest],
      ["kv-batch", kvRequest * 8], ["resident", weights + kvRequest * 8],
      ["time-72b", 2048 / 30.98], ["time-32b", 2048 / 31.82],
      ["time-32b-int4", 2048 / 35.66]
    ])
    for (const calculation of data.calculations) {
      expect(calculation.value).toBeCloseTo(expected.get(calculation.id)!, 10)
    }
    expect(kvRequest).toBe(10)
    expect(30720 + data.environment.outputTokens).toBe(model.defaultContext)
  })

  it("性能记录保留输入长度、设备数量与历史来源", () => {
    expect(data.environment.batchSize).toBe(1)
    const selected = data.vllmRows.filter((row) => row.inputTokens === 30720)
    expect(selected.find((row) => row.model === "72B" && row.precision === "GPTQ-Int4"))
      .toMatchObject({ gpus: 2, tokensPerSecond: 30.98 })
    expect(selected.find((row) => row.model === "32B" && row.precision === "BF16"))
      .toMatchObject({ gpus: 2, tokensPerSecond: 31.82 })
    expect(selected.find((row) => row.model === "32B" && row.precision === "GPTQ-Int4"))
      .toMatchObject({ gpus: 1, tokensPerSecond: 35.66 })
    for (const source of Object.values(data.sources)) {
      expect(new URL(source).protocol).toBe("https:")
      expect(source).toMatch(/\/blob\/[a-f0-9]{40}\//)
      expect(demoEvents.some((event) => event.text?.includes(source))).toBe(true)
    }
    expect(demoTask).toContain("2024 年 12 月 8 日")
  })
})

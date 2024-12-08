import data from "../../../../../docs/examples/qwen2.5-2024.json"
import type { ConversationEvent } from "./conversationStream"

const sources = data.sources

export const demoTask = `我们计划用两张 A100 80GB 做内部文档问答。请按 2024 年 12 月 8 日以前的公开资料，检查 Qwen2.5-72B-Instruct 能否满足下面的条件：8 个用户同时请求，每人输入约 30,720 tokens，再生成 2,048 tokens。

有同事认为，72B 的 BF16 权重约 135 GiB，两张卡能装下；模型卡又写着支持 128K，所以这样的请求应该没有问题。但官方测试里，同样是 72B，有的记录用两张卡，有的用三张或四张卡。请找到对应的原始数据，解释这些数字为什么不同。

需要算清楚 GQA 的 KV cache，说明输入、输出和并发分别占用多少内存；再查 72B GPTQ-Int4、32B BF16、32B GPTQ-Int4 在相同输入长度下的速度与卡数。我们希望一次完整答复在一分钟左右，不能把短输入、单用户的结果直接当作八用户服务指标。最后说明 32K 与 128K 的配置关系，以及这些 vLLM 数据能在多大程度上用于 MindPilot 的 MindNLP 本地路径。给出计算过程和原始出处，不需要采购报价。`

function toolResult(id: string, name: string, input: Record<string, unknown>, text: string): ConversationEvent[] {
  return [
    { type: "tool_start", run_id: id, name, input },
    { type: "tool_end", run_id: id, name, text }
  ]
}

function calculation(id: string): ConversationEvent[] {
  const item = data.calculations.find((item) => item.id === id)
  if (!item) throw new Error(`计算条目不存在：${id}`)
  return toolResult(id, "calculate", { text: item.expression }, String(item.value))
}

const transformersTable = [
  "| 输入 tokens | 精度 | A100 数量 | tokens/s | 显存（原表 GB） |",
  "| --- | --- | --- | --- | --- |",
  ...data.transformersRows.map((row) =>
    `| ${row.inputTokens.toLocaleString("en-US")} | ${row.precision} | ${row.gpus} | ${row.tokensPerSecond.toFixed(2)} | ${row.memoryGB.toFixed(2)} |`)
].join("\n")

const vllmTable = [
  "| 模型 | 输入 tokens | 精度 | A100 数量 | tokens/s | 设置 |",
  "| --- | --- | --- | --- | --- | --- |",
  ...data.vllmRows.filter((row) => row.inputTokens === 30720).map((row) =>
    `| ${row.model} | 30,720 | ${row.precision} | ${row.gpus} | ${row.tokensPerSecond.toFixed(2)} | ${row.setting} |`)
].join("\n")

const finalAnswer = `## 两张 A100 上的 Qwen2.5 部署条件

两张 A100 可以作为部分 72B 配置的运行设备。你提出的“8 个用户各占用 32K 上下文”需要单独计算：以 BF16 权重、16 位 KV cache、每个请求独立保存全部上下文为条件，仅权重和 KV cache 就约为 **215.41 GiB**。这已经超过两张 80GB 卡的容量，还没有计入临时张量与运行框架的其他占用。

### 显存计算

模型配置给出 80 层、64 个 Query heads、8 个 KV heads，hidden size 为 8,192，因此每个 head 的维度为 128。GQA 的 K、V 使用 8 个 heads。按每个元素 2 bytes 计算：

- 权重：72.7 × 10⁹ × 2 ÷ 1024³ ≈ **135.41 GiB**。72.7B 是模型卡取整后的参数规模，所以这里也是估算。
- 每个 token 的 KV cache：2 × 80 × 8 × 128 × 2 = **327,680 bytes**，即 0.3125 MiB。开头的 2 对应 K 与 V。
- 每个请求的长度上限：30,720 + 2,048 = **32,768 tokens**。完整保留该长度时，KV cache 约为 **10 GiB**。
- 8 个这样的请求合计约 **80 GiB**，加上权重约 **215.41 GiB**。

这里按所有请求都生成到长度上限、没有共享前缀、没有量化或转移 KV cache 的情况计算。调度器可以把部分请求放进等待队列，接收八个请求也不代表八个请求一直同时生成。GPTQ-Int4 主要降低权重占用；只有另外配置了 KV cache 的精度，缓存计算才会随之变化。[模型配置](${sources.config})

### 官方表里为什么会出现不同卡数

官方 Transformers 表中，72B BF16 在输入长度为 1 时使用两张卡，显存记录为 136.20 GB；输入 14,336 时使用三张卡，记录为 149.14 GB；输入 30,720 时也是三张卡，记录为 164.79 GB。后两个数字包含了更长请求的运行占用，比较时还要看分配到每张卡的情况。149.14 小于两张卡的标称容量之和，也不能证明这条三卡记录可直接改成两卡运行。[性能表](${sources.benchmark})

vLLM 的表格又使用了自己的配置。两卡 BF16 的 18.19 tokens/s 对应 **输入 1、max_model_len=4096、enforce_eager=True**；输入 30,720 的 BF16 记录使用四张卡，速度为 27.53 tokens/s。两条记录的输入、卡数和配置均不同。

### 相同长输入下的比较

统一到输入 30,720、输出 2,048、batch size=1，可以找到以下三条记录：

| 配置 | A100 数量 | 官方速度 | 2,048 ÷ 速度 |
| --- | --- | --- | --- |
| 72B GPTQ-Int4 | 2 | 30.98 tokens/s | 约 66.11 秒 |
| 32B BF16 | 2 | 31.82 tokens/s | 约 64.36 秒 |
| 32B GPTQ-Int4 | 1 | 35.66 tokens/s | 约 57.43 秒 |

其中 32B GPTQ-Int4 的官方单请求记录在一分钟以内。它使用一张卡，不能与两卡方案当作严格相同硬件条件下的模型速度比较；表格也没有回答量化后在你们文档问答任务中的准确率。

这些时间由公布的平均 tokens/s 反推。官方脚本对完整的 llm.generate 调用计时，平均速度则来自每轮输出长度除以该轮耗时，再取平均。因此上述数值是近似换算，不能当作原始延迟均值、首 token 时间或 P95。八用户的排队与吞吐需要另外统计。[计时代码](${sources.timer})

### 32K、128K 与 MindPilot

模型卡写明完整上下文能力为 131,072 tokens，但该版本 config.json 的 max_position_embeddings 为 32,768。超过默认长度时，模型卡给出的方案是在支持的框架中配置 YaRN，factor=4.0、original_max_position_embeddings=32768。输入和输出要共同满足长度限制；例如官方 128K 测试使用 129,024 输入加 2,048 输出。

当前这个 32K 请求本身不需要开启 128K。上下文上限提高后，实际请求保留的 token 数越多，KV cache 也越大。若同一个 72B 请求保留满 128K、KV 仍为 16 位，按相同公式缓存约为 40 GiB。[模型卡](${sources.modelCard})

这里引用的速度来自 A100 上的 vLLM 0.6.3、PyTorch 2.4.0 和 Transformers 4.46.0。MindPilot 的 MindNLP 本地加载路径使用另一套推理实现，因此这些数字适合解释容量和公开配置，不能直接作为该路径的实际速度，也不能据此认定它支持同样的 GPTQ 权重加载。

如果保留两张现有卡，建议把 **32B BF16 与 72B GPTQ-Int4** 放进同一套文档问答测试，记录引用准确率、长文遗漏、首次响应和完整响应时间；另用 32B GPTQ-Int4 检查单卡方案。最终选择取决于这些结果。就目前这组公开资料而言，能够支持的是各配置的单请求参考，尚不足以承诺八用户同时在一分钟内完成长文答复。

多步骤工具任务还有额外耗时：模型需要生成调用参数、等待工具返回，并带着新增结果继续生成。每一轮历史都会进入后续输入。部署检查因此还应包括完整工具调用过程，而不只测最后一段回答。[函数调用流程](${sources.functionCalling})`

export const demoEvents: ConversationEvent[] = [
  ...toolResult("benchmark", "search_internet", {
    query: "Qwen2.5-72B speed benchmark A100 80GB BF16 GPU memory input length 2024"
  }, `Qwen2.5 Speed Benchmark · 2024-12-04 版本

测试使用 NVIDIA A100 80GB；batch size=1，生成长度为 2,048 tokens。输入长度分别为 1、6,144、14,336、30,720、63,488、129,024。以下为 Transformers 的 72B 记录：

${transformersTable}

原表将显存列标为 GB；vLLM 部分不提供该列，因为其测试配置会预分配显存。[原始表格](${sources.benchmark})`),
  ...toolResult("config", "search_internet", {
    query: "Qwen2.5-72B-Instruct config.json num_hidden_layers num_key_value_heads hidden_size 2024"
  }, `Qwen2.5-72B-Instruct · config.json / 模型卡 · 2024-09-25 版本

参数规模：${data.model.parametersBillions}B；num_hidden_layers=${data.model.layers}；hidden_size=${data.model.hiddenSize}；num_attention_heads=${data.model.queryHeads}；num_key_value_heads=${data.model.kvHeads}；torch_dtype=bfloat16；max_position_embeddings=${data.model.defaultContext}。

[config.json](${sources.config}) · [模型卡](${sources.modelCard})`),
  ...calculation("weights"),
  ...calculation("kv-token"),
  ...calculation("kv-request"),
  ...calculation("kv-batch"),
  ...calculation("resident"),
  ...toolResult("context", "search_internet", {
    query: "Qwen2.5-72B-Instruct default context 32768 128K long text configuration 2024"
  }, `模型卡的 Processing Long Texts 段落给出默认 32,768 的配置，并在支持的推理框架中使用 YaRN 扩展长上下文。对应参数为 factor=4.0、original_max_position_embeddings=32768、type=yarn。该版本说明 vLLM 使用 static YaRN，长度扩展配置可能影响较短文本。

模型卡标明完整上下文 131,072 tokens、生成上限 8,192 tokens。[原始说明](${sources.modelCard})`),
  ...toolResult("vllm", "search_internet", {
    query: "Qwen2.5 72B 32B vLLM input length 30720 GPTQ-Int4 BF16 speed benchmark"
  }, `vLLM 表 · 输入 30,720 tokens，输出 2,048 tokens，batch size=1

${vllmTable}

Default：gpu_memory_utilization=0.9，max_model_len=32768，enforce_eager=False。另有 72B BF16 的两卡记录：输入 1，18.19 tokens/s，Setting 1 将 max_model_len 设为 4096。[原始数据与参数](${sources.benchmark})`),
  ...calculation("time-72b"),
  ...calculation("time-32b"),
  ...calculation("time-32b-int4"),
  ...toolResult("timer", "search_internet", {
    query: "QwenLM Qwen2.5 speed_benchmark_vllm.py run_infer collect_statistics Average Throughput"
  }, `speed_benchmark_vllm.py：run_infer 在 llm.generate 调用前后读取时间，返回 time_cost；collect_statistics 对每轮 out_length / time_cost 求平均。

测试环境：A100 80GB、CUDA ${data.environment.cuda}、vLLM ${data.environment.vllm}、PyTorch ${data.environment.torch}、Transformers ${data.environment.transformers}。表中没有八用户并发的延迟分布。[计时代码](${sources.timer}) · [测试条件](${sources.benchmark})`),
  ...toolResult("function-call", "search_internet", {
    query: "Qwen2.5 function calling Qwen-Agent tool results messages extend December 2024"
  }, `官方 Function Calling 文档展示了查询当前气温及次日气温的连续过程：模型输出函数名和 JSON 参数；程序执行函数；将 function 结果追加到 messages；再次调用模型得到最终回答。

Qwen-Agent 2024-12-06 版本的 function_calling.py 明确配置 qwen2.5-72b-instruct，并保留工具结果进入下一轮消息的实现。[官方调用过程](${sources.functionCalling}) · [72B 示例代码](${sources.agentExample})`),
  { type: "answer", text: finalAnswer }
]

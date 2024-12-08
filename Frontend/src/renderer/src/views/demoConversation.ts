export const demoTask = "为 50 人研发团队制定离线知识库方案：核查内部需求与 2024 年公开资料，对比 Qwen2.5-72B、32B、7B；计算权重内存和两套年度预算，检查矛盾，给出带来源的决策与验收清单。预算上限 30 万元，数据不得离开内网。"

export const demoEvents = [
  { type: "tool_start", run_id: "kb", name: "search_local_knowledgebase", input: { database: "研发知识库", query: "并发需求、保密边界、现有设备与年度预算" } },
  { type: "tool_end", run_id: "kb", name: "search_local_knowledgebase", text: "需求核对完成：50 名成员，峰值 8 路请求；本地文档 18,400 份；离线运行；年度预算 300,000 元。[内部需求 §2–4]" },
  { type: "tool_start", run_id: "papers", name: "arxiv", input: { query: "Self-RAG; retrieval augmented generation evaluation; before 2024-12-08" } },
  { type: "tool_end", run_id: "papers", name: "arxiv", text: "研究资料分组：检索质量、引用可追溯性、生成结果核查；建立独立验收维度。[研究资料摘要]" },
  { type: "tool_start", run_id: "web", name: "search_internet", input: { query: "Qwen2.5 72B 32B 7B 官方模型卡；截止 2024-12-08" } },
  { type: "tool_end", run_id: "web", name: "search_internet", text: "资料归类：模型卡、部署文档、检索研究。Qwen2.5-72B 的参数规模为 72.7B；权重容量与运行总内存分别记录，不混用。[Qwen 模型卡]" },
  { type: "tool_start", run_id: "memory", name: "calculate", input: { text: "72.7e9 * 2 / 1024**3" } },
  { type: "tool_end", run_id: "memory", name: "calculate", text: "FP16 权重约 135.4 GiB，另需 KV cache 与运行内存。" },
  { type: "tool_start", run_id: "budget-a", name: "calculate", input: { text: "220000 + 800*8*250/1000*0.8 + 24000" } },
  { type: "tool_end", run_id: "budget-a", name: "calculate", text: "方案 A：245,280 元，预算余额 54,720 元。" },
  { type: "tool_start", run_id: "budget-b", name: "calculate", input: { text: "140000 + 750*8*250/1000*0.8 + 18500" } },
  { type: "tool_end", run_id: "budget-b", name: "calculate", text: "方案 B：159,700 元，预算余额 140,300 元。" },
  { type: "tool_start", run_id: "check", name: "search_local_knowledgebase", input: { database: "研发知识库", query: "核查 8 路并发与显存约束；输出验收条件" } },
  { type: "tool_end", run_id: "check", name: "search_local_knowledgebase", text: "交叉核查完成：将权重估算与并发验收分别列出；两套预算均低于 30 万元。采购条件包含团队文档评测与离线运行验收。[验收清单]" },
  { type: "answer", text: "## 离线知识库部署决策\n**推荐：Qwen2.5-72B + 中文混合检索，按实测并发结果确定设备配置。**\n\n1. **方案 A · 72B**：年度预算 **245,280 元**，预算余额 **54,720 元**。适用于复杂资料综合与多步骤工具任务。\n2. **方案 B · 32B**：年度预算 **159,700 元**，预算余额 **140,300 元**。设备 140,000 元 + 电费 1,200 元 + 维护 18,500 元。\n3. **核查结论**：135.4 GiB 仅为 72B 的 FP16 权重估算，不能当作 8 路并发的总显存需求；公开指标不能代替团队文档上的评测。\n4. **验收清单**：中文检索命中、引用对应原文、错误问题拒答、8 路请求延迟、断网启动、工具失败与恢复。\n\n**交付内容**：两套预算明细 · 模型适用条件 · 来源对应表 · 六项验收清单" }
] as const

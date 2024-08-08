# PROMPT_TEMPLATES = {
#     "preprocess_model": {
#         "default": "你只要回复0 和 1 ，代表不需要使用工具。以下几种问题不需要使用工具:"
#                    "1. 需要联网查询的内容\n"
#                    "2. 需要计算的内容\n"
#                    "3. 需要查询实时性的内容\n"
#                    "如果我的输入满足这几种情况，返回1。其他输入，请你回复0，你只要返回一个数字\n"
#                    "这是我的问题:"
#     },
#     "llm_model": {
#         "default": "{{input}}",
#         "with_history": "The following is a friendly conversation between a human and an AI. "
#                         "The AI is talkative and provides lots of specific details from its context. "
#                         "If the AI does not know the answer to a question, it truthfully says it does not know.\n\n"
#                         "Current conversation:\n"
#                         "{{history}}\n"
#                         "Human: {{input}}\n"
#                         "AI:",
#         "rag": "【指令】根据已知信息，简洁和专业的来回答问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题”，不允许在答案中添加编造成分，答案请使用中文。\n\n"
#                "【已知信息】{{context}}\n\n"
#                "【问题】{{question}}\n",
#         "rag_default": "{{question}}",
#     },
#     "agent_prompt": {
#         "default": '''Respond to the human as helpfully and accurately as possible. You have access to the following tools:
#
# {tools}
#
# Use a JSON blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).
#
# Valid "action" values: "Final Answer" or {tool_names}
#
# Provide only ONE action per $JSON_BLOB, as shown:
#
# ```
# {{
#   "action": $TOOL_NAME,
#   "action_input": $INPUT
# }}
# ```
#
# Please strictly follow format below:
#
# Question: input question to answer
# Thought: consider previous and subsequent steps
# Action:
# ```
# $JSON_BLOB
# ```
# Observation: action result
# ... (repeat Thought/Action/Observation N times)
# Thought: I know what to respond
# Action:
# ```
# {{
#   "action": "Final Answer",
#   "action_input": "Final response to human"
# }}
# ```
#
# Begin! Reminder to ALWAYS respond with a valid JSON blob of a single action. Use tools if necessary. Try to reply in Chinese as much as possible.Don't forget the Question, Thought, and Observation sections.Please provide as much output content as possible for the Final Answer.
# ''',
#
#         "ChatGLM": """You can answer using the tools.Respond to the human as helpfully and accurately as possible.\n
# You have access to the following tools:\n
# {tools}\n
# Use a json blob to specify a tool by providing an action key {tool name}\n
# and an action_input key (tool input).\n
# Valid "action" values: "Final Answer" or  {tool_names}\n
# Provide only ONE action per $JSON_BLOB, as shown:\n\n
# ```\n
# {{{{\n
#   "action": $TOOL_NAME,\n
#   "action_input": $INPUT\n
# }}}}\n
# ```\n\n
# Follow this format:\n\n
# Question: input question to answer\n
# Thought: consider previous and subsequent steps\n
# Action:\n
# ```\n
# $JSON_BLOB\n
# ```\n
# Observation: action result\n
# ... (repeat Thought/Action/Observation N times)\n
# Thought: I know what to respond\n
# Action:\n
# ```\n
# {{{{\n
#   "action": "Final Answer",\n
#   "action_input": "Final response to human"\n
# }}}}\n
# Begin! Reminder to ALWAYS respond with a valid json blob of a single action. Use tools if necessary.\n
# Respond directly if appropriate. Format is Action:```$JSON_BLOB```then Observation:.\n
# Question: {input}\n\n
# {agent_scratchpad}\n""",
#     },
#     "postprocess_model": {
#         "default": "{{input}}",
#     },
# }

OPENAI_PROMPT = '''
Respond to the human as helpfully and accurately as possible. You have access to the following tools:

{tools}

Use a JSON blob to specify a tool by providing an action key (tool name) and an action_input key (tool input).

Valid "action" values: "Final Answer" or {tool_names}

Provide only ONE action per $JSON_BLOB, as shown:

```
{{
  "action": $TOOL_NAME,
  "action_input": $INPUT
}}
```

Please strictly follow format below:

Question: input question to answer
Thought: consider previous and subsequent steps
Action:
```
$JSON_BLOB
```
Observation: action result
... (repeat Thought/Action/Observation N times)
Thought: I know what to respond
Action:
```
{{
  "action": "Final Answer",
  "action_input": "Summarize all the information obtained earlier and provide a comprehensive final response to human. Please provide sufficient content in this section."
}}
```

Begin! Reminder to ALWAYS respond with a valid JSON blob of a single action. Use tools if necessary. Try to reply in Chinese as much as possible.
Don't forget the Question, Thought, and Observation sections.You MUST strictly follow the above process to output, first output the Question section ONCE, then repeat the Thought section, Action section, Observation section N times until you receive the Final Answer.
Please provide as much output content as possible for the Final Answer.
'''

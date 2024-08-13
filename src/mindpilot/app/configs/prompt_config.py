PROMPT_TEMPLATES = {
    "llm_model": {
        "default": "{{input}}",
        "with_history": "The following is a friendly conversation between a human and an AI. "
                        "The AI is talkative and provides lots of specific details from its context. "
                        "If the AI does not know the answer to a question, it truthfully says it does not know."
                        "Please reply in Chinese.\n\n"
                        "Current conversation:\n"
                        "{{chat_history}}\n"
                        "Human: {{input}}\n"
                        "AI:",
    }
}

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

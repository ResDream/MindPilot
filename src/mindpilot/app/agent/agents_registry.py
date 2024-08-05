import typing
from typing import List, Sequence

import langchain_core
from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool

from langchain_core.prompts import SystemMessagePromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, PromptTemplate
def agents_registry(
        llm: BaseLanguageModel,
        tools: Sequence[BaseTool] = [],
        callbacks: List[BaseCallbackHandler] = [],
        prompt: str = None,
        verbose: bool = False,
):
    prompt = ChatPromptTemplate(
        input_variables=['agent_scratchpad', 'input', 'tool_names', 'tools'],
        optional_variables=['chat_history'],
        input_types={'chat_history': typing.List[typing.Union[
            langchain_core.messages.ai.AIMessage, langchain_core.messages.human.HumanMessage, langchain_core.messages.chat.ChatMessage, langchain_core.messages.system.SystemMessage, langchain_core.messages.function.FunctionMessage, langchain_core.messages.tool.ToolMessage]]},
        partial_variables={'chat_history': []},
        metadata={},
        messages=[
            SystemMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['tool_names', 'tools'],
                    template='''
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
  "action_input": "Final response to human"
}}
```

Begin! Reminder to ALWAYS respond with a valid JSON blob of a single action. Use tools if necessary. Try to reply in Chinese as much as possible.Don't forget the Question, Thought, and Observation sections.Please provide as much output content as possible for the Final Answer.
''',
                )
            ),
            MessagesPlaceholder(variable_name='chat_history', optional=True),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['agent_scratchpad', 'input'],
                    template='''
{input}

{agent_scratchpad}
(reminder to respond in a JSON blob no matter what)
'''
                )
            )
        ]
    )
    # print(prompt)

    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=verbose, callbacks=callbacks, handle_parsing_errors=True
    )

    return agent_executor

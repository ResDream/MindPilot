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
                    template=prompt,
                )
            ),
            MessagesPlaceholder(variable_name='chat_history', optional=True),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate(
                    input_variables=['agent_scratchpad', 'input'],
                    template='''{input}\n\n{agent_scratchpad}\n(reminder to respond in a JSON blob no matter what)\n'''
                )
            )
        ]
    )

    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=verbose, callbacks=callbacks, handle_parsing_errors=True
    )

    return agent_executor

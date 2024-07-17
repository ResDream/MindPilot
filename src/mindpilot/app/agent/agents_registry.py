from typing import List, Sequence

from langchain import hub
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool


def agents_registry(
        llm: BaseLanguageModel,
        tools: Sequence[BaseTool] = [],
        callbacks: List[BaseCallbackHandler] = [],
        prompt: str = None,
        verbose: bool = False,
):
    if prompt is not None:
        prompt = ChatPromptTemplate.from_messages([SystemMessage(content=prompt)])
    else:
        prompt = hub.pull("hwchase17/structured-chat-agent")  # default prompt
    agent = create_structured_chat_agent(llm=llm, tools=tools, prompt=prompt)

    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=verbose, callbacks=callbacks, handle_parsing_errors=True
    )

    return agent_executor

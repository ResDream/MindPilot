# Langchain 自带的 Wolfram Alpha API 封装

from ..pydantic_v1 import Field
from app.utils import get_tool_config
from .tools_registry import BaseToolOutput, regist_tool


@regist_tool
def wolfram(query: str = Field(description="The formula to be calculated")):
    """Useful for when you need to calculate difficult formulas"""

    from langchain.utilities.wolfram_alpha import WolframAlphaAPIWrapper

    appid = get_tool_config("appid")
    wolfram = WolframAlphaAPIWrapper(
        wolfram_alpha_appid=appid
    )
    ans = wolfram.run(query)
    return BaseToolOutput(ans)

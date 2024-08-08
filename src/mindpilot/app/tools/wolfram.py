# Langchain 自带的 Wolfram Alpha API 封装

from src.mindpilot.app.utils.pydantic_v1 import Field

from .tools_registry import BaseToolOutput, regist_tool
from ..utils.system_utils import get_tool_config


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

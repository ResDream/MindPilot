const conversationSummaryQueryPrompt: string = `\n \n \n \n 请总结以上内容，总结的内容精炼且不超过5个字，并以以下JSON格式输出：\n \n
{
  "summary": "对话的总结内容"
}`;

const axiosHanders = {
  "accept": "application/json",
  "Content-Type": "application/json"
};


export const conversationSummary = async (chatConversation: string) => {

  console.log("Conversation summary: ", chatConversation);

  const requestPrompt = chatConversation + conversationSummaryQueryPrompt;
  const requestBody = {
    query: requestPrompt,
    history: [],
    stream: false,
    agent_enable: false,
    tool_config: [],
    chat_model_config: {
      api_key: "sk-cERDW9Fr2ujq8D2qYck9cpc9MtPytN26466bunfYXZVZWV7Y",
      base_url: "https://api.chatanywhere.tech/v1/",
      is_openai: true,
      llm_model: {
        "gpt-4o": {
          callbacks: true,
          max_tokens: 8192,
          temperature: 0.8
        }
      },
      platform: "OpenAI",

      agent_id: -1
    }
  };

  try {
    const response = await fetch("http://127.0.0.1:7861/chat/chat/online", {
      method: "POST",
      headers: {
        ...axiosHanders
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    const responseData = await response.json();
    const messageContent = responseData.choices[0].message.content;
    //正则匹配messageContent中可能的json结构
    const jsonMatch = messageContent.match(/\{.*\}/s);
    console.log("jsonMatch", jsonMatch);
    if (jsonMatch) {
      const jsonObject = JSON.parse(jsonMatch[0]);
      console.log(jsonObject);
      return jsonObject;
    }
  } catch (error) {
    console.error("Error summarizing conversation:", error);
    return "总结失败";
  }
};

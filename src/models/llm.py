"""
LLM配置模块
提供通义千问模型的初始化和配置

对应Spring AI的：
@Resource
private ChatClient chatClient;
"""
from langchain_community.chat_models import ChatTongyi
from langchain.schema import HumanMessage, SystemMessage
import os


def get_llm(model_name="qwen-plus", temperature=0.7, streaming=False):
    """
    获取通义千问LLM实例

    这是LangChain中最核心的概念之一：ChatModel
    - 在Spring AI中，你用ChatClient来调用模型
    - 在LangChain中，你用ChatTongyi（或ChatOpenAI等）

    参数说明：
    - model_name: 模型名称，qwen-plus是通义千问的中等模型
    - temperature: 温度参数，控制输出的随机性（0-1，越高越随机）
    - streaming: 是否启用流式输出（类似Spring AI的.stream()）

    Args:
        model_name: 模型名称，默认qwen-plus
        temperature: 温度参数，默认0.7
        streaming: 是否流式输出，默认False

    Returns:
        ChatTongyi实例
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise ValueError(
            "未找到DASHSCOPE_API_KEY环境变量。"
            "请在.env文件中配置：DASHSCOPE_API_KEY=your_key"
        )

    return ChatTongyi(
        model_name=model_name,
        dashscope_api_key=api_key,
        temperature=temperature,
        streaming=streaming
    )


# 使用示例
if __name__ == "__main__":
    """
    测试LLM是否正常工作

    对比Spring AI：
    String response = chatClient.prompt()
        .system("你是一个企业差旅助手")
        .user("你好")
        .call()
        .content();

    LangChain的方式：
    1. 创建消息列表（SystemMessage + HumanMessage）
    2. 调用llm.invoke()
    3. 获取response.content
    """
    print("测试通义千问LLM...")

    try:
        llm = get_llm()

        # LangChain使用消息列表的方式
        messages = [
            SystemMessage(content="你是一个企业差旅助手"),
            HumanMessage(content="你好，请简单介绍一下你自己")
        ]

        response = llm.invoke(messages)
        print(f"\n回答：{response.content}")

        print("\n✅ LLM测试成功！")

    except Exception as e:
        print(f"\n❌ LLM测试失败：{e}")
        print("\n请检查：")
        print("1. 是否已安装依赖：pip install -r requirements.txt")
        print("2. 是否已配置.env文件中的DASHSCOPE_API_KEY")

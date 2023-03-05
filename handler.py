# https://qiita.com/w2or3w/items/1b80bfbae59fe19e2015
import os
import json
import openai
import logging
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextMessage, TextSendMessage
from langchain import ConversationChain
from langchain.llms import OpenAIChat
from langchain.agents import initialize_agent
from langchain.agents import load_tools
from langchain.agents import ZeroShotAgent, Tool, AgentExecutor
from langchain.chains.conversation.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain import GoogleSearchAPIWrapper, LLMChain

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set OpenAI API key and Line API access token
openai.api_key = os.environ["OPENAI_API_KEY"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

agent_memory = {}


def create_agent(event):
    # LLMの準備
    llm = OpenAIChat(temperature=0)
    tools = load_tools(["google-search", "llm-math"], llm=llm)
    conversation = ConversationChain(
        llm=llm, memory=ConversationSummaryMemory(llm=llm), verbose=True
    )
    agent = initialize_agent(
        tools,
        llm,
        agent="zero-shot-react-description",
        verbose=True,
        return_intermediate_steps=True,
    )
    search = GoogleSearchAPIWrapper()
    tools = [
        Tool(
            name="Search",
            func=search.run,
            description="useful for when you need to answer questions about current events",
        )
    ]
    prefix = f"""あなたは役に立つアシスタントです。人間と会話をし、以下の質問にできる限り答えてください。あなたは以下のツールを利用することができます。"""
    suffix = """始めましょう。質問には日本語で答えてください。"
指示与えられたウェブ検索結果を使って、与えられた質問に対する包括的な返答を書くこと。
検索結果の引用は、引用文献の後に`* URL`表記を必ず用いること。
また、検索結果が同名の複数のテーマで構成されている場合は、各テーマごとに分けて回答してください。
{chat_history}
質問: {input}
{agent_scratchpad}"""
    prompt = ZeroShotAgent.create_prompt(
        tools,
        prefix=prefix,
        suffix=suffix,
        input_variables=["input", "chat_history", "agent_scratchpad"],
    )
    memory = ConversationBufferMemory(memory_key="chat_history")
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    agent_chain = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=True, memory=memory
    )
    return agent_chain


# Define Lambda function handler
def lambda_handler(event, context):
    global agent_memory
    # logger.info(event)
    # Extract input text from the event
    try:
        event_body = json.loads(event["body"])
        user_id = event_body["events"][0]["source"]["userId"]
        reply_token = event_body["events"][0]["replyToken"]
        input_text = event_body["events"][0]["message"]["text"]

        # Check if user is in the memory cache
        if user_id not in agent_memory:
            agent_memory[user_id] = {"agent": create_agent(event)}

        agent = agent_memory[user_id]["agent"]

        keywords = ["教えて", "ください", "?", "？"]
        if any(keyword in input_text for keyword in keywords):
            # Send the response message back to LINE
            output_text = agent.run(input=input_text)
            line_bot_api.reply_message(reply_token, TextSendMessage(text=str(output_text)))

    except Exception as e:
        logger.exception(e)
        line_bot_api.reply_message(reply_token, TextSendMessage(text=f"何かエラーが起きたようです{str(e)}"))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "ok"}),
    }

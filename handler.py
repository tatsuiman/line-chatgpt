# https://qiita.com/w2or3w/items/1b80bfbae59fe19e2015
import json
import os
import openai
import urllib.request
import logging
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextMessage, TextSendMessage


# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Set OpenAI API key and Line API access token
openai.api_key = os.environ["OPENAI_API_KEY"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

memory = {}

# Define Lambda function handler
def lambda_handler(event, context):
    global memory
    #logger.info(event)
    # Extract input text from the event
    try:
        event_body = json.loads(event["body"])
        user_id = event_body["events"][0]["source"]["userId"]
        input_text = event_body["events"][0]["message"]["text"]

        # Check if user is in the memory cache
        if user_id not in memory:
            memory[user_id] = {"messages": []}

        # Add the input message to the user's messages
        past_messages = memory[user_id]["messages"]
        if len(past_messages) == 0:
            past_messages.append({"role": "system", "content": "あなたは役に立つアシスタントです。"})
        past_messages.append({"role": "user", "content": input_text})

        if "ください" in input_text or "？" in input_text or "?" in input_text:
            # Use OpenAI to generate a response
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=past_messages)
            output_text = response["choices"][0]["message"]["content"]
            past_messages.append({"role": "assistant", "content": output_text})

            # Send the response message back to LINE
            reply_token = event_body["events"][0]["replyToken"]
            line_bot_api.reply_message(reply_token, TextSendMessage(text=output_text))

        memory[user_id]["messages"] = past_messages

    except Exception as e:
        logger.exception(e)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "ok"}),
    }

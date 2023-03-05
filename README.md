# ChatGPT Line Bot

## setup
1. Copy the env.template file to create a new .env file.
```bash
cp env.template .env
```
2. Open the .env file in a text editor and enter your API keys.
```bash
vim .env
```
3. Input your OpenAI API Key to OPENAI_API_KEY
```bash
OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxx
```
4. Create Line Channel Access Token
* https://qiita.com/w2or3w/items/1b80bfbae59fe19e2015
```bash
LINE_CHANNEL_ACCESS_TOKEN="channel access token"
```

5. Input your Google Custom Search ID to GOOGLE_CSE_ID and Google Custom Search API Key to GOOGLE_API_KEY
```bash
GOOGLE_CSE_ID=xxxxxxxxxxxxxxxxxxx
GOOGLE_API_KEY=xxxxxxxxxxxxxxxxxxx
```

## deploy
```bash
yarn
sls deploy --stage dev
```

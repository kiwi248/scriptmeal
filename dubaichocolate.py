import os
from dotenv import load_dotenv
load_dotenv()

# 0.2.x 버전에서는 이걸 쓰세요
from langchain_openai import ChatOpenAI
#from langchain.chat_models import ChatOpenAI
from langchain.agents import load_tools, initialize_agent, AgentType
#from langchain_community.tools import DuckDuckGoSearchRun

llm = ChatOpenAI(
    temperature=0,
    model_name='gpt-4',
)

tools = load_tools(["wikipedia"], llm=llm)
#tools = [DuckDuckGoSearchRun()] 기능안좋다

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

agent.run("두바이 스타일 초콜렛을 간단히 설명해줘. 반드시 한국어로 답변해줘")
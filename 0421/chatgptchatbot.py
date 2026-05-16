import streamlit as st
#from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

st.set_page_config(page_title="🍳 레시피 챗봇")
st.title('🍳 레시피 챗봇')

import os
from dotenv import load_dotenv
load_dotenv() 

def generate_response(input_text):
    llm = ChatOpenAI(temperature=0,
                     model_name='gpt-4',
                    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 친절한 레시피챗봇입니다. 요리이름, 조리시간, 재료, 조리상세순서(숫자 붙여서)를 포함한 답을 주세요. 한국어로 주세요."),
        ("human", "{question}")
    ])

    chain = prompt | llm
    response = chain.invoke({"question": input_text})
    st.info(response.content)

with st.form('Question'):
    text = st.text_area('질문 입력:', '')
    submitted = st.form_submit_button('보내기')
    if submitted:
        generate_response(text)
# ------------------------------------------------------
# Streamlit
# Knowledge Bases for Amazon Bedrock and LangChain 🦜️🔗
# ------------------------------------------------------

import boto3
import logging
import os
import streamlit as st
from langchain_openai import ChatOpenAI
from typing import List, Dict
from pydantic import BaseModel
from operator import itemgetter
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_aws import ChatBedrock
from langchain_aws import AmazonKnowledgeBasesRetriever
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

st.set_page_config(
    page_title='RowdyLLM',
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# ------------------------------------------------------
# Log level

logging.getLogger().setLevel(logging.ERROR) # reduce log level

# ------------------------------------------------------
# Amazon Bedrock - settings

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
)

retrieval_runtime = boto3.client(
    service_name="bedrock-agent-runtime",
    region_name="us-east-1",
    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
)

model_id = "anthropic.claude-3-haiku-20240307-v1:0"

model_kwargs =  { 
    "max_tokens": 2048,
    "temperature": 0.0,
    "top_k": 250,
    "top_p": 1,
    "stop_sequences": ["\n\nHuman"],
}

# ------------------------------------------------------
# LangChain - RAG chain with chat history

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are Rowdy the Riverhawk, a chatbot for the University of Massachusetts Lowell."
         "Provide answers in the style of a tour guide. If the answer isn't in the search results, say 'I'm not sure what you mean'. Never tell the user that you searched anything. Here is some context:\n {context}"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ]
)

# Amazon Bedrock - KnowledgeBase Retriever 
retriever = AmazonKnowledgeBasesRetriever(
    knowledge_base_id=st.secrets["KB_ID"], # 👈 Set your Knowledge base ID
    client=retrieval_runtime,
    retrieval_config={"vectorSearchConfiguration": {"numberOfResults": 4}},
)

match (st.secrets["MODEL"]):
    case "OPENAI":
        model = ChatOpenAI(model_name="gpt-4o")
    case "ANTHROPIC":
        model = ChatBedrock(
            client=bedrock_runtime,
            model_id=model_id,
            model_kwargs=model_kwargs,
        )

chain = (
    RunnableParallel({
        "context": itemgetter("question") | retriever,
        "question": itemgetter("question"),
        "history": itemgetter("history"),
    })
    .assign(response = prompt | model | StrOutputParser())
    .pick(["response", "context"])
)

# Streamlit Chat Message History
history = StreamlitChatMessageHistory(key="chat_messages")

# Chain with History
chain_with_history = RunnableWithMessageHistory(
    chain,
    lambda session_id: history,
    input_messages_key="question",
    history_messages_key="history",
    output_messages_key="response",
)

# ------------------------------------------------------
# Pydantic data model and helper function for Citations

class Citation(BaseModel):
    page_content: str
    metadata: Dict

def extract_citations(response: List[Dict]) -> List[Citation]:
    return [Citation(page_content=doc.page_content, metadata=doc.metadata) for doc in response]

# Initialize session state for messages if not already present
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Ask me anything about UMass Lowell!"}]

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat Input - User Prompt 
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    config = {"configurable": {"session_id": "any"}}
    # Chain - Stream
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ''
        for chunk in chain_with_history.stream(
            {"question" : prompt, "history" : history},
            config
        ):
            if 'response' in chunk:
                full_response += chunk['response']
                placeholder.markdown(full_response)
            else:
                full_context = chunk['context']
        placeholder.markdown(full_response)
        # Citations with S3 pre-signed URL
        citations = extract_citations(full_context)
        with st.expander("Show source details >"):
            for citation in citations:
                st.write("Page Content:", citation.page_content)
                st.write("Score:", citation.metadata['score'])
                st.write("URL:", citation.metadata['source_metadata']['url'])
        # session_state append
        st.session_state.messages.append({"role": "assistant", "content": full_response})
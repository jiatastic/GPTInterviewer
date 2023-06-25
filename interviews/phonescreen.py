import langchain.chat_models.base
from PyPDF2 import PdfReader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import NLTKTextSplitter
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
import streamlit as st
class phonescreen:

    def __init__(self, pdf_file, retriever = None):
        self.pdf_file = pdf_file
        self.retriever = None

    def Chat_OpenAI(self, query: str, llm: langchain.chat_models.base.BaseChatModel, chain_type_kwargs: dict, retriever, memory):

            # Conversational Retrieval chain
            qa = RetrievalQA.from_chain_type(llm= llm, chain_type_kwargs = chain_type_kwargs, chain_type = 'stuff', retriever = retriever, memory = memory)

            answers = qa.run(query)

            return answers
# langchain: https://python.langchain.com/
from langchain.memory import ConversationBufferMemory
# Audio recording
from dataclasses import dataclass
# Streamlit - for web application
import streamlit as st
from st_audiorec.st_custom_components import st_audiorec
from speech_recognition.openai_whisper import save_wav_file, transcribe
from audio_recorder_streamlit import audio_recorder
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain, RetrievalQA
from prompts.prompts import templates
from langchain.prompts.prompt import PromptTemplate
from typing import Literal
from azure_service.speech_synthesizer import speech_synthesizer
from azure.cognitiveservices.speech import AudioDataStream
from streamlit_lottie import st_lottie
import json
import nltk
from langchain.text_splitter import NLTKTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

nltk.download("punkt")
### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
st_lottie(load_lottiefile("images/hello.json"), speed=1, reverse=False, loop=True, quality="high", height=300)

st.markdown("### Instruction: ")
st.markdown("""
    In this session, the GPT Interviewer will assess your soft skills as they relate to the job description.
    - Press the microphone to start answering.
    - Each Interview will take 10 to 15 mins. 
    - Start introduce yourself and enjoy！ """)
st.markdown("""
    """)

bjd = st.text_area("""#### Please enter the job description here: 
                    If you don't have one, enter keywords, such as "communication" or "teamwork" instead. """)

### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

@dataclass
class Message:
    """Class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str

def save_vector(text):

    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)

    # Create emebeddings
    embeddings = OpenAIEmbeddings()

    docsearch = FAISS.from_texts(texts, embeddings)

    # Retrieve embeedings from vector database - Chromadb
    #vectordb = Chroma.from_texts(texts=texts, embedding=embeddings, persist_directory= 'db')
    #vectordb.persist()
    #vectordb = Chroma(persist_directory='db', embedding_function=embeddings)

    return docsearch

def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def initialize_session_state():

    if 'bjd_docsearch' not in st.session_state:
        st.session_state.bjd_docserch = save_vector(bjd)

    if 'bjd_retriever' not in st.session_state:
        st.session_state.bjd_retriever = st.session_state.bjd_docserch.as_retriever(search_type="similarity")

    if 'bjd_chain_type_kwargs' not in st.session_state:
        Behavioral_Prompt = PromptTemplate(input_variables=["context", "question"],
                                          template=templates.behavioral_template)
        st.session_state.bjd_chain_type_kwargs = {"prompt": Behavioral_Prompt}
    # interview history
    if "history" not in st.session_state:
        st.session_state.history = []

    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0

    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationBufferMemory()

    if 'guideline' not in st.session_state:

        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.6, )

        st.session_state.guideline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type_kwargs=st.session_state.bjd_chain_type_kwargs, chain_type='stuff',
            retriever=st.session_state.bjd_retriever, memory=st.session_state.memory).run(
            "Create an interview guideline and prepare total of 8 questions. Make sure the questions tests the soft skills")

    # llm chain and memory
    if "conversation" not in st.session_state:

        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.8,)

        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template="""I want you to act as an interviewer strictly following the guideline in the current conversation.
                            Do not ask the same question.
                            Do not repeat the question.
                            Do ask follow-up questions if necessary. 
                            You name is GPTInterviewer.
                            I want you to only reply as an interviewer.
                            Do not write all the conversation at once. 
                            I want you to only reply as an interviewer.
                            Ask me questions and wait for my answers. Do not write explanations.

                            Current Conversation:
                            {history}

                            Candidate: {input}
                            AI: """)

        st.session_state.conversation = ConversationChain(prompt=PROMPT, llm=llm,
                                                       memory=st.session_state.memory)

    if "feedback" not in st.session_state:

        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.5,)

        st.session_state.feedback = ConversationChain(
            prompt=PromptTemplate(input_variables = ["history", "input"], template = templates.feedback_template),
            llm=llm,
            memory = st.session_state.memory,
        )

if bjd:

    # initialize session states
    initialize_session_state()
    load_css()

    chat_placeholder = st.container()
    answer_placeholder = st.container()
    credit_card_placeholder = st.empty()

    def answer_call_back():

        with get_openai_callback() as cb:
            # user input
            human_answer = st.session_state.answer
            # transcribe audio
            save_wav_file("temp/audio.wav", human_answer)

            try:
                input = transcribe("temp/audio.wav")
            except:
                st.write("Sorry, I didn't get that. Please try again.")

            # save human_answer to history
            st.session_state.history.append(
                Message("human", input)
            )

            # OpenAI answer and save to history
            llm_answer = st.session_state.conversation.run(input)
            # speech synthesis and speak out
            interviewer_answer = speech_synthesizer(llm_answer)
            # save audio data
            stream = AudioDataStream(interviewer_answer)
            # save audio data to history
            st.session_state.history.append(
                Message("ai", llm_answer)
            )
            st.session_state.token_count += cb.total_tokens

    if len(st.session_state.history) < 11:

        with answer_placeholder:
            answer = audio_recorder(pause_threshold = 2.5, sample_rate = 44100)
            if answer:
                st.session_state['answer'] = answer
                answer_call_back()

        with chat_placeholder:

            for answer in st.session_state.history:
                if answer:
                    div = f"""<div class="chat-row 
                                    {'' if answer.origin == 'ai' else 'row-reverse'}">
                                    <img class="chat-icon" src="static/{
                    'chat.png' if answer.origin == 'ai'
                    else 'user.png'}"
                                         width=32 height=32>
                                    <div class="chat-bubble
                                    {'ai-bubble' if answer.origin == 'ai' else 'human-bubble'}">
                                        &#8203;{answer.message}
                                    </div>
                                </div>
                                        """
                    st.markdown(div, unsafe_allow_html=True)

                for _ in range(3):
                    st.markdown("")

        credit_card_placeholder.caption(f"""
        Used {st.session_state.token_count} tokens \n
        """)
    else:
        conclusion = "Thank you for using GPTInterviewer. Please enter you email address to receive the report."
        conclusion = speech_synthesizer(conclusion)

        # submit email address
        with st.form(key='my_form'):
            email = st.text_input("Email")
            submit = st.form_submit_button("Submit")

            if submit:
                conclusion = None
                evaluation = st.session_state.feedback.run("please give evalution regarding the interview")
                st.write(evaluation)
                st.stop()
else:
    st.write("Please enter the job description first")





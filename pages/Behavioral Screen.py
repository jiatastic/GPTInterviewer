# langchain: https://python.langchain.com/
from langchain.memory import ConversationBufferMemory
# Audio recording
from dataclasses import dataclass
# Streamlit - for web application
import streamlit as st
from speech_recognition.openai_whisper import save_wav_file, transcribe
from audio_recorder_streamlit import audio_recorder
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain, RetrievalQA
from prompts.prompts import templates
from langchain.prompts.prompt import PromptTemplate
from typing import Literal
from aws.synthesize_speech import synthesize_speech
from streamlit_lottie import st_lottie
import json
import nltk
from langchain.text_splitter import NLTKTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import base64
from IPython.display import Audio

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

bjd = st.text_area("""Please enter the job description here (If you don't have one, enter keywords, such as "communication" or "teamwork" instead): """)

### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
@dataclass
class Message:
    """Class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str

def autoplay_audio(file_path: str):
    def update_audio():
        global global_audio_md
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            global_audio_md = f"""
                <audio controls autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
    def update_markdown(audio_md):
        st.markdown(audio_md, unsafe_allow_html=True)
    update_audio()
    update_markdown(global_audio_md)

def save_vector(text):

    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
    # Create emebeddings
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def load_css():
    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

def initialize_session_state():

    if "bjd_docsearch" not in st.session_state:
        st.session_state.bjd_docserch = save_vector(bjd)

    if "bjd_retriever" not in st.session_state:
        st.session_state.bjd_retriever = st.session_state.bjd_docserch.as_retriever(search_type="similarity")

    if "bjd_chain_type_kwargs" not in st.session_state:
        Behavioral_Prompt = PromptTemplate(input_variables=["context", "question"],
                                          template=templates.behavioral_template)
        st.session_state.bjd_chain_type_kwargs = {"prompt": Behavioral_Prompt}

    # interview history
    if "history" not in st.session_state:
        st.session_state.history = []

    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0

    if "memory" not in st.session_state:
        st.session_state.memory = ConversationBufferMemory()

    if "guideline" not in st.session_state:

        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.8, )

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
                            
                            Ask me questions and wait for my answers. Do not write explanations.
                            Ask question like a real person, only one question at a time.
                            Do not ask the same question.
                            Do not repeat the question.
                            Do ask follow-up questions if necessary. 
                            You name is GPTInterviewer.
                            I want you to only reply as an interviewer.
                            Do not write all the conversation at once.
                            If there is an error, point it out.

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

def answer_call_back():
    with get_openai_callback() as cb:
        # user input
        human_answer = st.session_state.answer
        # transcribe audio
        save_wav_file("temp/audio.wav", human_answer)
        try:
            input = transcribe("temp/audio.wav")
            # save human_answer to history
            st.session_state.history.append(
                Message("human", input)
            )
            # OpenAI answer and save to history
            llm_answer = st.session_state.conversation.run(input)
            # speech synthesis and speak out
            audio_file_path = synthesize_speech(llm_answer)
            # 创建自动播放的音频部件
            audio_widget = Audio(audio_file_path, autoplay=True)
            # save audio data to history
            st.session_state.history.append(
                Message("ai", llm_answer)
            )
            st.session_state.token_count += cb.total_tokens
        except:
            st.session_state.history.append(Message("ai", "Sorry, I didn't get that. Please try again."))

        return audio_widget

### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

if bjd:

    # initialize session states
    initialize_session_state()
    load_css()

    chat_placeholder = st.container()
    answer_placeholder = st.container()
    credit_card_placeholder = st.empty()

    with st.form(key = "email"):
        email = st.text_input("Please enter your email address to access inte rview report (you may enter it anytime during the interview): ")
        submit = st.form_submit_button("Submit")

    # if submit email adress, get interview feedback imediately
    if submit:
        if submit:
            evaluation = st.session_state.feedback.run("please give evalution regarding the interview")
            st.markdown(evaluation)
            st.stop()

    # keep interview
    else:
        with answer_placeholder:
            answer = audio_recorder(pause_threshold=2.5, sample_rate=44100)
            if answer:
                st.session_state['answer'] = answer
                audio_widget = answer_call_back()
            else:
                st.write("Please speak into the microphone to answer the question.")

        with chat_placeholder:
            for answer in st.session_state.history:
                if answer:
                    if answer.origin == 'ai':
                        div = f"""<div class="chat-row">
                                        <img class="chat-icon" src="static/images/chat.png" width=32 height=32>
                                        <div class="chat-bubble ai-bubble">
                                            &#8203;{answer.message}
                                        </div>
                                    </div>
                                    """
                        st.markdown(div, unsafe_allow_html=True)
                        st.write(audio_widget)

                    else:
                        div = f"""<div class="chat-row row-reverse">
                                        <img class="chat-icon" src="static/images/user.png" width=32 height=32>
                                        <div class="chat-bubble human-bubble">
                                            &#8203;{answer.message}
                                        </div>
                                    </div>
                                    """
                        st.markdown(div, unsafe_allow_html=True)
                for _ in range(3):
                    st.markdown("")

        credit_card_placeholder.caption(f"""
        Progress: {int(len(st.session_state.history) / 30 * 100)} % completed \n
        """)

else:
    st.write("Please enter the job description first")





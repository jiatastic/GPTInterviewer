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
from langchain.text_splitter import NLTKTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import base64
from IPython.display import Audio
import nltk

### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
st_lottie(load_lottiefile("images/welcome.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
jd = st.text_area("""Please enter the job description here (If you don't have one, enter keywords, such as "communication" or "teamwork" instead): """)
auto_play = st.checkbox("Let AI interviewer speak! (Please don't switch during the interview)")

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

def save_vector(text: str):
    nltk.download('punkt')
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
    # Create emebeddings
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def initialize_session_state():
    if "bq_docsearch" not in st.session_state:
        st.session_state.bq_docserch = save_vector(jd)
    if "bq_retriever" not in st.session_state:
        st.session_state.bq_retriever = st.session_state.bq_docserch.as_retriever(search_type="similarity")
    if "bq_chain_type_kwargs" not in st.session_state:
        Behavioral_Prompt = PromptTemplate(input_variables=["context", "question"],
                                          template=templates.behavioral_template)
        st.session_state.bq_chain_type_kwargs = {"prompt": Behavioral_Prompt}
    # interview history
    if "history" not in st.session_state:
        st.session_state.history = []
        st.session_state.history.append(Message("ai", "Hello there! I am your interviewer today. I will access your soft skills through a series of questions. Let's get started! Please start by saying hello or introducing yourself. Note: The maximum length of your answer is 4097 tokens!"))

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
            chain_type_kwargs=st.session_state.bq_chain_type_kwargs, chain_type='stuff',
            retriever=st.session_state.bq_retriever, memory=st.session_state.memory).run(
            "Create an interview guideline and prepare total of 8 questions. Make sure the questions tests the soft skills")
    # llm chain and memory
    if "conversation" not in st.session_state:
        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.8,)
        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template="""I want you to act as an interviewer strictly following the guideline in the current conversation.
                            Candidate has no idea what the guideline is.
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
        if voice:
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
                # create audio widget with autoplay
                audio_widget = Audio(audio_file_path, autoplay=True)
                # save audio data to history
                st.session_state.history.append(
                    Message("ai", llm_answer)
                )
                st.session_state.token_count += cb.total_tokens
                return audio_widget
            except:
                st.session_state.history.append(Message("ai", "Sorry, I didn't get that. Please try again."))
        else:
            input = human_answer
            st.session_state.history.append(
                Message("human", input)
            )
            # OpenAI answer and save to history
            llm_answer = st.session_state.conversation.run(input)
            # OpenAI answer and save to history
            llm_answer = st.session_state.conversation.run(input)
            # speech synthesis and speak out
            audio_file_path = synthesize_speech(llm_answer)
            # create audio widget with autoplay
            audio_widget = Audio(audio_file_path, autoplay=True)
            # save audio data to history
            st.session_state.history.append(
                Message("ai", llm_answer)
            )
            st.session_state.token_count += cb.total_tokens
            return audio_widget

### ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if jd:
    # initialize session states
    initialize_session_state()
    credit_card_placeholder = st.empty()
    feedback = st.button("Get Interview Feedback")
    guideline = st.button("Show me interview guideline")
    audio = None
    chat_placeholder = st.container()
    answer_placeholder = st.container()
    if guideline:
        st.write(st.session_state.guideline)
    # if submit email adress, get interview feedback imediately
    if feedback:
        evaluation = st.session_state.feedback.run("please give evalution regarding the interview")
        st.markdown(evaluation)
        st.stop()
    # keep interview
    else:
        with answer_placeholder:
            voice: bool = st.checkbox("I would like to speak with AI Interviewer!")
            if voice:
                answer = audio_recorder(pause_threshold=2.5, sample_rate=44100)
            else:
                answer = st.chat_input("Your answer")
            if answer:
                st.session_state['answer'] = answer
                audio = answer_call_back()
        with chat_placeholder:
            for answer in st.session_state.history:
                if answer.origin == 'ai':
                    if auto_play and audio:
                        with st.chat_message("assistant"):
                            st.write(answer.message)
                            st.write(audio)
                    else:
                        with st.chat_message("assistant"):
                            st.write(answer.message)
                else:
                    with st.chat_message("user"):
                        st.write(answer.message)

        credit_card_placeholder.caption(f"""
                        Total Used Tokens: {st.session_state.token_count} \n
                        Progress: {int(len(st.session_state.history) / 30 * 100)}% completed.
        """)

else:
    st.info("Please submit job description to start interview.")





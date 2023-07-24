# langchain: https://python.langchain.com/
from dataclasses import dataclass
import streamlit as st
from speech_recognition.openai_whisper import save_wav_file, transcribe
from st_audiorec.st_custom_components import st_audiorec
from audio_recorder_streamlit import audio_recorder
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA, ConversationChain
from prompts.prompts import templates
from langchain.prompts.prompt import PromptTemplate
from typing import Literal
from aws.synthesize_speech import synthesize_speech
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import NLTKTextSplitter
import nltk
from streamlit_lottie import st_lottie
import json
import time
from IPython.display import Audio

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
st_lottie(load_lottiefile("images/welcome.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
jd = st.text_area("Please enter the job description here (If you don't have one, enter keywords, such as PostgreSQL or Python instead): ")
auto_play = st.checkbox("Let AI interviewer speak! (Please don't switch during the interview)")

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
@dataclass
class Message:
    """class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str

def save_vector(text):
    """embeddings"""

    nltk.download('punkt')
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
     # Create emebeddings
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def initialize_session_state():
    """ initialize session states """
    if 'jd_docsearch' not in st.session_state:
        st.session_state.jd_docserch = save_vector(jd)
    if 'jd_retriever' not in st.session_state:
        st.session_state.jd_retriever = st.session_state.jd_docserch.as_retriever(search_type="similarity")
    if 'jd_chain_type_kwargs' not in st.session_state:
        Interview_Prompt = PromptTemplate(input_variables=["context", "question"],
                                          template=templates.jd_template)
        st.session_state.jd_chain_type_kwargs = {"prompt": Interview_Prompt}
    if 'jd_memory' not in st.session_state:
        st.session_state.jd_memory = ConversationBufferMemory()
    # interview history
    if "jd_history" not in st.session_state:
        st.session_state.jd_history = []
        st.session_state.jd_history.append(Message("ai",
                                                   "Hello, Welcome to the interview. I am your interviewer today. I will ask you professional questions regarding the job description you submitted."
                                                   "Please start by introducting a little bit about yourself. Note: The maximum length of your answer is 4097 tokens!"))
    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0
    if "jd_guideline" not in st.session_state:
        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.8,)
        st.session_state.jd_guideline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type_kwargs=st.session_state.jd_chain_type_kwargs, chain_type='stuff',
            retriever=st.session_state.jd_retriever, memory = st.session_state.jd_memory).run("Create an interview guideline and prepare only one questions for each topic. Make sure the questions tests the technical knowledge")
    # llm chain and memory
    if "jd_screen" not in st.session_state:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.8, )
        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template="""I want you to act as a human interviewer strictly following the guideline in the current conversation.
                            
                            Ask me questions and wait for my answers.
                            Do not write explanations.
                            only one question at a time.
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

        st.session_state.jd_screen = ConversationChain(prompt=PROMPT, llm=llm,
                                                           memory=st.session_state.jd_memory)
    if 'jd_feedback' not in st.session_state:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.8, )
        st.session_state.jd_feedback = ConversationChain(
            prompt=PromptTemplate(input_variables=["history", "input"], template=templates.feedback_template),
            llm=llm,
            memory=st.session_state.jd_memory,
        )

def answer_call_back():
    """ answer call back function"""
    with get_openai_callback() as cb:
        # user input
        human_answer = st.session_state.answer
        if voice:
            # transcribe audio
            save_wav_file("temp/audio.wav", human_answer)
            try:
                input = transcribe("temp/audio.wav")
                # save human_answer to history
                st.session_state.jd_history.append(
                    Message("human", input)
                )
                # OpenAI answer and save to history
                llm_answer = st.session_state.jd_screen.run(input)
                # speech synthesis
                audio_file_path = synthesize_speech(llm_answer)
                st.session_state.audio_file_path = audio_file_path
                # 创建自动播放的音频部件
                audio_widget = Audio(audio_file_path, autoplay=True)
                # save audio data to history
                st.session_state.jd_history.append(
                    Message("ai", llm_answer)
                )
                st.session_state.token_count += cb.total_tokens
                return audio_widget
            except:
                st.session_state.jd_history.append(Message("ai", "Sorry, I didn't get that. Please try again."))
        else:
            input = human_answer
            st.session_state.jd_history.append(
                Message("human", input)
            )
            # OpenAI answer and save to history
            llm_answer = st.session_state.jd_screen.run(input)
            # speech synthesis
            audio_file_path = synthesize_speech(llm_answer)
            st.session_state.audio_file_path = audio_file_path
            # 创建自动播放的音频部件
            audio_widget = Audio(audio_file_path, autoplay=True)
            # save audio data to history
            st.session_state.jd_history.append(
                Message("ai", llm_answer)
            )
            st.session_state.token_count += cb.total_tokens
            return audio_widget

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
# sumitted job description
if jd:
    # initialize session states
    initialize_session_state()
    #st.write(st.session_state.jd_guideline)
    credit_card_placeholder = st.empty()
    feedback = st.button("Get Interview Feedback")
    guideline = st.button("Show me interview guideline!")
    chat_placeholder = st.container()
    answer_placeholder = st.container()
    audio = None
    # if submit email adress, get interview feedback imediately
    if guideline:
        st.write(st.session_state.jd_guideline)
    if feedback:
        evaluation = st.session_state.jd_feedback.run("please give evalution regarding the interview")
        st.markdown(evaluation)
        st.stop()
    else:
        with answer_placeholder:
            voice: bool = st.checkbox("I would like to speak with AI Interviewer")
            if voice:
                answer = audio_recorder(pause_threshold = 2.5, sample_rate = 44100)
            else:
                answer = st.chat_input("Your answer")
            if answer:
                st.session_state['answer'] = answer
                audio = answer_call_back()
        with chat_placeholder:
            for answer in st.session_state.jd_history:
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
        Used {st.session_state.token_count} tokens \n
        Progress: {int(len(st.session_state.jd_history) / 30 * 100)}% completed.""")
else:
    st.info("Please submit a job description to start the interview.")
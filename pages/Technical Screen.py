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

nltk.download('punkt')

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

st_lottie(load_lottiefile("images/hello.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
st.markdown("### Instruction: ")
st.markdown("""
    In this session, the GPT Interviewer will assess your technical skills as they relate to the job description.
    - Press the microphone to start answering.
    - Each Interview will take 10 to 15 mins. 
    - Start introduce yourself and enjoy！ """)
jd = st.text_area("Please enter the job description here (If you don't have one, enter keywords, such as PostgreSQL or Python instead): ")

with st.sidebar:
    st.markdown("### What's next?")
    st.write("""
                For example, if the job description requires knowledge of data mining, GPT Interviewer will ask you questions like "Explains overfitting or How does backpropagation work?" 
             """)

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
@dataclass
class Message:

    """class for keeping track of interview history."""

    origin: Literal["human", "ai"]
    message: str

def save_vector(text):

    """embeddings"""

    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
     # Create emebeddings
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def load_css():

    """ Load CSS """

    with open("static/styles.css", "r") as f:
        css = f"<style>{f.read()}</style>"
        st.markdown(css, unsafe_allow_html=True)

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
    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0
    if "jd_guideline" not in st.session_state:
        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.6,)
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

        st.session_state.jd_screen = ConversationChain(prompt=PROMPT, llm=llm,
                                                           memory=st.session_state.jd_memory)
    if 'jd_feedback' not in st.session_state:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.5, )
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
            # speech synthesis and speak out
            interviewer_answer = synthesize_speech(llm_answer)

            # save audio data to history
            st.session_state.jd_history.append(
                Message("ai", llm_answer)
            )
            st.session_state.token_count += cb.total_tokens
        except:
            st.session_state.jd_history.append(Message("ai", "Sorry, I didn't get that. Please try again."))

### ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

# sumitted job description
if jd:

    # initialize session states
    initialize_session_state()
    load_css()
    #st.write(st.session_state.jd_guideline)

    chat_placeholder = st.container()
    answer_placeholder = st.container()
    credit_card_placeholder = st.empty()

    with st.form(key = "email"):
        email = st.text_input("Please enter your email address to access interview report (you may enter it anytime during the interview): ")
        submit = st.form_submit_button("Submit")

    # if submit email adress, get interview feedback imediately
    if submit:
        evaluation = st.session_state.feedback.run("please give evalution regarding the interview")
        st.markdown(evaluation)
        st.stop()
    else:
        with answer_placeholder:
            answer = audio_recorder(pause_threshold = 2.5, sample_rate = 44100)
            if answer:
                st.session_state['answer'] = answer
                answer_call_back()
            else:
                st.write("Your interview history will be displaced here")

        with chat_placeholder:
            for answer in st.session_state.jd_history:
                if answer:
                    div = f"""<div class="chat-row 
                                    {'' if answer.origin == 'ai' else 'row-reverse'}">
                                    <img class="chat-icon" src="static/images{
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
        Progress: {int((len(st.session_state.jd_history) / 11 ** 100))}% completed.""")
else:
    st.write("Please enter the job description first.")

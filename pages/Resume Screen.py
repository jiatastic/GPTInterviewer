# langchain: https://python.langchain.com/
from dataclasses import dataclass
import streamlit as st
from speech_recognition.openai_whisper import save_wav_file, transcribe
from audio_recorder_streamlit import audio_recorder
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts.prompt import PromptTemplate
from prompts.prompts import templates
from typing import Literal
from aws.synthesize_speech import synthesize_speech
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import NLTKTextSplitter
from PyPDF2 import PdfReader
from prompts.prompt_selector import prompt_sector
from streamlit_lottie import st_lottie
import json
from IPython.display import Audio
import nltk


def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)
st_lottie(load_lottiefile("images/welcome.json"), speed=1, reverse=False, loop=True, quality="high", height=300)

#st.markdown("""solutions to potential errors:""")
with st.expander("""Why did I encounter errors when I tried to talk to the AI Interviewer?"""):
    st.write("""This is because the app failed to record. Make sure that your microphone is connected and that you have given permission to the browser to access your microphone.""")
with st.expander("""Why did I encounter errors when I tried to upload my resume?"""):
    st.write("""
    Please make sure your resume is in pdf format. More formats will be supported in the future.
    """)

st.markdown("""\n""")
position = st.selectbox("Select the position you are applying for", ["Data Analyst", "Software Engineer", "Marketing"])
resume = st.file_uploader("Upload your resume", type=["pdf"])
auto_play = st.checkbox("Let AI interviewer speak! (Please don't switch during the interview)")

#st.toast("4097 tokens is roughly equivalent to around 800 to 1000 words or 3 minutes of speech. Please keep your answer within this limit.")

@dataclass
class Message:
    """Class for keeping track of interview history."""
    origin: Literal["human", "ai"]
    message: str

def save_vector(resume):
    """embeddings"""
    nltk.download('punkt')
    pdf_reader = PdfReader(resume)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    # Split the document into chunks
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)
    embeddings = OpenAIEmbeddings()
    docsearch = FAISS.from_texts(texts, embeddings)
    return docsearch

def initialize_session_state_resume():
    # convert resume to embeddings
    if 'docsearch' not in st.session_state:
        st.session_state.docserch = save_vector(resume)
    # retriever for resume screen
    if 'retriever' not in st.session_state:
        st.session_state.retriever = st.session_state.docserch.as_retriever(search_type="similarity")
    # prompt for retrieving information
    if 'chain_type_kwargs' not in st.session_state:
        st.session_state.chain_type_kwargs = prompt_sector(position, templates)
    # interview history
    if "resume_history" not in st.session_state:
        st.session_state.resume_history = []
        st.session_state.resume_history.append(Message(origin="ai", message="Hello, I am your interivewer today. I will ask you some questions regarding your resume and your experience. Please start by saying hello or introducing yourself. Note: The maximum length of your answer is 4097 tokens!"))
    # token count
    if "token_count" not in st.session_state:
        st.session_state.token_count = 0
    # memory buffer for resume screen
    if "resume_memory" not in st.session_state:
        st.session_state.resume_memory = ConversationBufferMemory(human_prefix = "Candidate: ", ai_prefix = "Interviewer")
    # guideline for resume screen
    if "resume_guideline" not in st.session_state:
        llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.5,)

        st.session_state.resume_guideline = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type_kwargs=st.session_state.chain_type_kwargs, chain_type='stuff',
            retriever=st.session_state.retriever, memory = st.session_state.resume_memory).run("Create an interview guideline and prepare only two questions for each topic. Make sure the questions tests the knowledge")
    # llm chain for resume screen
    if "resume_screen" not in st.session_state:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.7, )

        PROMPT = PromptTemplate(
            input_variables=["history", "input"],
            template= """I want you to act as an interviewer strictly following the guideline in the current conversation.
            
            Ask me questions and wait for my answers like a human. Do not write explanations.
            Candidate has no assess to the guideline.
            Only ask one question at a time. 
            Do ask follow-up questions if you think it's necessary.
            Do not ask the same question.
            Do not repeat the question.
            Candidate has no assess to the guideline.
            You name is GPTInterviewer.
            I want you to only reply as an interviewer.
            Do not write all the conversation at once.
            Candiate has no assess to the guideline.
            
            Current Conversation:
            {history}
            
            Candidate: {input}
            AI: """)
        st.session_state.resume_screen =  ConversationChain(prompt=PROMPT, llm = llm, memory = st.session_state.resume_memory)
    # llm chain for generating feedback
    if "resume_feedback" not in st.session_state:
        llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.5,)
        st.session_state.resume_feedback = ConversationChain(
            prompt=PromptTemplate(input_variables=["history","input"], template=templates.feedback_template),
            llm=llm,
            memory=st.session_state.resume_memory,
        )

def answer_call_back():
    with get_openai_callback() as cb:
        human_answer = st.session_state.answer
        if voice:
            save_wav_file("temp/audio.wav", human_answer)
            try:
                input = transcribe("temp/audio.wav")
                # save human_answer to history
            except:
                st.session_state.resume_history.append(Message("ai", "Sorry, I didn't get that."))
                return "Please try again."
        else:
            input = human_answer
        st.session_state.resume_history.append(
            Message("human", input)
        )
        # OpenAI answer and save to history
        llm_answer = st.session_state.resume_screen.run(input)
        # speech synthesis and speak out
        audio_file_path = synthesize_speech(llm_answer)
        # create audio widget with autoplay
        audio_widget = Audio(audio_file_path, autoplay=True)
        # save audio data to history
        st.session_state.resume_history.append(
            Message("ai", llm_answer)
        )
        st.session_state.token_count += cb.total_tokens
        return audio_widget

if position and resume:
    # intialize session state
    initialize_session_state_resume()
    credit_card_placeholder = st.empty()
    col1, col2 = st.columns(2)
    with col1:
        feedback = st.button("Get Interview Feedback")
    with col2:
        guideline = st.button("Show me interview guideline!")
    chat_placeholder = st.container()
    answer_placeholder = st.container()
    audio = None
    # if submit email adress, get interview feedback imediately
    if guideline:
        st.markdown(st.session_state.resume_guideline)
    if feedback:
        evaluation = st.session_state.resume_feedback.run("please give evalution regarding the interview")
        st.markdown(evaluation)
        st.download_button(label="Download Interview Feedback", data=evaluation, file_name="interview_feedback.txt")
        st.stop()
    else:
        with answer_placeholder:
            voice: bool = st.checkbox("I would like to speak with AI Interviewer!")
            if voice:
                answer = audio_recorder(pause_threshold=2, sample_rate=44100)
                #st.warning("An UnboundLocalError will occur if the microphone fails to record.")
            else:
                answer = st.chat_input("Your answer")
            if answer:
                st.session_state['answer'] = answer
                audio = answer_call_back()

        with chat_placeholder:
            for answer in st.session_state.resume_history:
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
                        Progress: {int(len(st.session_state.resume_history) / 30 * 100)}% completed.""")


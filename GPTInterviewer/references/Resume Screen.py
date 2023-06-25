# langchain: https://python.langchain.com/
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import NLTKTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import os
import nltk
from PyPDF2 import PdfReader
# Audio recording
from elevenlabs import generate
import wave
# Streamlit - for web application
import streamlit as st
from st_audiorec.st_custom_components import st_audiorec
from prompts.prompts import templates
from prompts.prompt_selector import prompt_sector
from interviews.phonescreen import phonescreen
from speech_recognition.openai_whisper import save_wav_file, transcribe
from audio_recorder_streamlit import audio_recorder

if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt')

# Check if temp folder exists
os.makedirs('../temp', exist_ok=True)


def save_vector(resume):
    pdf_reader = PdfReader(resume)
    text = ""

    for page in pdf_reader.pages:
        text += page.extract_text()

    # Split the document into chunks
    text_splitter = NLTKTextSplitter()
    texts = text_splitter.split_text(text)

    # Create emebeddings
    embeddings = OpenAIEmbeddings()

    # Retrieve embeedings from vector database - Chromadb
    vectordb = Chroma.from_texts(texts=texts, embedding=embeddings)

    #vectordb.persist()

    #vectordb = Chroma(persist_directory='db', embedding_function=embeddings)

    return vectordb


class Config:

    '''Configurations for memory buffer and llm'''

    # Memory Buffer
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    llm = ChatOpenAI(
        model_name = "gpt-3.5-turbo",
        temperature = 0.8,)

def main():

    # Title
    st.header('Phone Screen')

    # Select Posistion
    position = st.selectbox('please select your desired position', ['Data Analyst/Data Scientist', 'Software Engineer', 'Marketing'])

    # Resume upload
    st.markdown("### Resume")
    resume = st.file_uploader("upload your resume here ☁", type = 'pdf')

    # Introduction
    intro = """ Hello, I am your AI Interviewer. Please submit your resume, and then start recording to introduce yourself. When you are finished, press stop.

    Here is a more detailed explanation of each step:

    - Submit your resume: Please upload your resume to the interview platform. This will allow the AI Interviewer to learn more about your skills and experience.
    - Say Hi and tell the interviewer you are ready for the interview! 
    - Answering: Press start recording to answer question and press stop when you are finished. If the microphone is not working, please click reset and try again."""

    st.markdown(intro)

    if resume:

        # interview object with submitted resume
        interview = phonescreen(resume)

        if interview:

            # convert resume into embeddings
            vectordb = save_vector(resume)
            st.cache(vectordb)

            retriever = vectordb.as_retriever()
            chain_type_kwargs = prompt_sector(position, templates)

        if retriever and chain_type_kwargs:

            # Recordings from User
            wav_audio_data = audio_recorder()

            if wav_audio_data:
                save_wav_file("temp/audio.wav", wav_audio_data)
                transcription = transcribe("temp/audio.wav")

                if transcription:
                    # st.write(transcription)
                    response = interview.Chat_OpenAI(query = transcription, memory = Config.memory, llm = Config.llm, chain_type_kwargs = chain_type_kwargs, retriever = retriever)
                    audio_response = generate(response, voice = "Bella", model="eleven_monolingual_v1")
                    st.markdown("### AI Interviewer: ")
                    st.audio(audio_response)

                else:
                    st.text("Please check your Microphone")
            else:
                st.text("Click start recording to answer!")

    # Evaluation 
    st.markdown("### Post-Interview Evalution")
    st.write("We are working on post-interview evaluation. We will add this feature in next two weeks.")

    print(Config.memory)

if __name__ == "__main__":
    main()
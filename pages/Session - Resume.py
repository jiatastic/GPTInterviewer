import streamlit as st
from speech_recognition.openai_whisper import save_wav_file, transcribe
from langchain.callbacks import get_openai_callback
from aws.synthesize_speech import synthesize_speech
from IPython.display import Audio
from dataclasses import dataclass
import base64
from typing import Literal
from audio_recorder_streamlit import audio_recorder
from initialization import initialize_session_state
from prompts.prompts import templates
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
            llm_answer = st.session_state.screen.run(input)
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

position = st.selectbox("#### position", ["Data Analyst", "Software Engineer", "Marketing"])
resume = st.file_uploader("#### resume", type=["pdf"])
st.session_state.resume = resume

chat_placeholder = st.container()
answer_placeholder = st.container()
credit_card_placeholder = st.empty()

if st.session_state.resume:
    initialize_session_state(position=position)
    if st.button("Get Feeback"):
        evaluation = st.session_state.feedback.run("please give evalution regarding the interview")
        st.markdown(evaluation)
        st.stop()
        for key in st.session_state.keys():
            del st.session_state[key]
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
                if answer.origin == 'ai':
                    with st.chat_message("assistant"):
                        st.write(answer.message)
                        st.write(audio_widget)
                else:
                    with st.chat_message("user"):
                        st.write(answer.message)
            credit_card_placeholder.caption(f"""
               Used {st.session_state.token_count} tokens \n
               Progress: {int(len(st.session_state.history) / 30 * 100)}% completed.""")
else:
    st.info("Please upload your resume and select desired position to start the interview.")

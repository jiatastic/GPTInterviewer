import streamlit as st
from streamlit_option_menu import option_menu
from app_utils import switch_page
from initialization import initialize_session_state, embedding, resume_reader
from prompts.prompts import templates
from typing import Literal
from dataclasses import dataclass
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

# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
st.set_page_config(page_title = "🤖 AI Interviewer", layout = "centered")

home_title = "🤖 AI Interviewer"
home_introduction = "Welcome to AI Interviewer, empowering your interview preparation with generative AI."

with st.sidebar:
    st.markdown('🤖 AI Interviewer - V0.1.2')
    st.markdown("""  
    #### Let's contact:
    [Haoxiang Jia](https://www.linkedin.com/in/haoxiang-jia/)
    
    [Zicheng Wang](https://www.linkedin.com/in/todd-wang-5001aa264/)
    #### Please fill the form, we'd love to have your feedback:
    [Feedback Form](https://docs.google.com/forms/d/13f4q03bk4lD7sKR7qZ8UM1lQDo6NhRaAKv7uIeXHEaQ/edit)

    #### What's next?
    #### Powered by

    [OpenAI](https://openai.com/)

    [FAISS](https://github.com/facebookresearch/faiss)

    [Langchain](https://github.com/hwchase17/langchain)

                """)

st.markdown(
    "<style>#MainMenu{visibility:hidden;}</style>",
    unsafe_allow_html=True
)

st.markdown(f"""# {home_title} <span style=color:#2E9BF5><font size=5>Beta</font></span>""",unsafe_allow_html=True)
st.markdown("""\n""")
#st.markdown("#### Greetings")
st.markdown("Welcome to AI Interviewer! 👏AI Interviewer is a generative AI powered tool that provides you with realistic interview experience. "
            "You can upload your resume and enter job descriptions, AI Interviewer will ask you customized questions. In addition, you can configure your own AI Interviewer!")
st.markdown("#### Get started!")
st.markdown("Select one of the following screens to start your interview!")

selected = option_menu(
        menu_title= None,
        options=["Professional", "Resume", "Behavioral","Customize!"],
        icons = ["cast", "cloud-upload", "cast"],
        default_index=0,
        orientation="horizontal",
    )

# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Professional':
    st.info("""
        📚In this session, the AI Interviewer will assess your technical skills as they relate to the job description.
        - Press the microphone to start answering.
        - Each Interview will take 10 to 15 mins. 
        - Start introduce yourself and enjoy！ """)
    if st.button("Start Interview!"):
        switch_page("Professional Screen")

# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Resume':
    st.info("""
    📚In this session, the AI Interviewer will review your resume and discuss your past experiences.
    - Press the microphone to start answering.
    - Each Interview will take 10 to 15 mins. 
    - Start introduce yourself and enjoy！ """
    )
    if st.button("Start Interview!"):
        switch_page("Resume Screen")

# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Behavioral':
    st.info("""
    📚In this session, the AI Interviewer will assess your soft skills as they relate to the job description.
    - Press the microphone to start answering.
    - Each Interview will take 10 to 15 mins. 
    - Start introduce yourself and enjoy！ 
    """)
    if st.button("Start Interview!"):
        switch_page("Behavioral Screen")

if selected == 'Customize!':
    st.info("""
        📚In this session, you can customize your own AI Interviewer and practice with it!
         - Configure AI Interviewer in different specialties.
         - Configure AI Interviewer in different personalities.
         - Different tones of voice.
         
         Coming at the end of July""")
import streamlit as st
from streamlit_option_menu import option_menu
from app_utils import switch_page
import streamlit as st
from PIL import Image

# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————

im = Image.open("icon.png")
st.set_page_config(page_title = "AI Interviewer", layout = "centered",page_icon=im)

home_title = "AI Interviewer"
home_introduction = "Welcome to AI Interviewer, empowering your interview preparation with generative AI."

with st.sidebar:
    st.markdown('AI Interviewer - V0.1.2')
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
st.image(im, width=100)
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
        - To start a new session, just refresh the page.
        - Start introduce yourself and enjoy！ """)
    if st.button("Start Interview!"):
        switch_page("Professional Screen")

# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Resume':
    st.info("""
    📚In this session, the AI Interviewer will review your resume and discuss your past experiences.
    - Press the microphone to start answering.
    - Each Interview will take 10 to 15 mins.
    - To start a new session, just refresh the page.
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
    - To start a new session, just refresh the page.
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
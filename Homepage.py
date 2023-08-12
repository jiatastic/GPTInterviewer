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
st.markdown("Welcome to AI Interviewer! 👏 AI Interviewer is your personal interviewer powered by generative AI that conducts mock interviews."
            "You can upload your resume and enter job descriptions, and AI Interviewer will ask you customized questions. Additionally, you can configure your own Interviewer!")

st.markdown("""\n""")
with st.expander("Updates"):
    st.write("""
    - Chat support
    - You can now view interview guideline during the interview""")
with st.expander("What's coming next?"):
    st.write("""
    - We're aware the current evaluation system is not very satisfying. We're working on a better evaluation system that will be released soon!
    - We're thinking about a way for you to save your interview history and view your progress. Stay tuned!
    - Interviews are boring. We're working on a customization system that will allow you to customize your own AI Interviewer!""")
st.markdown("""\n""")
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
        Note: The maximum length of your answer is 4097 tokens!
        - Each Interview will take 10 to 15 mins.
        - To start a new session, just refresh the page.
        - Choose your favorite interaction style (chat/voice)
        - Start introduce yourself and enjoy！ """)
    if st.button("Start Interview!"):
        switch_page("Professional Screen")

# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Resume':
    st.info("""
    📚In this session, the AI Interviewer will review your resume and discuss your past experiences.
    Note: The maximum length of your answer is 4097 tokens!
    - Each Interview will take 10 to 15 mins.
    - To start a new session, just refresh the page.
    - Choose your favorite interaction style (chat/voice)
    - Start introduce yourself and enjoy！ """
    )
    if st.button("Start Interview!"):
        switch_page("Resume Screen")

# ————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
if selected == 'Behavioral':
    st.info("""
    📚In this session, the AI Interviewer will assess your soft skills as they relate to the job description.
    Note: The maximum length of your answer is 4097 tokens!
    - Each Interview will take 10 to 15 mins.
    - To start a new session, just refresh the page.
    - Choose your favorite interaction style (chat/voice)
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
# ——————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————————
st.markdown("""\n""")
st.markdown("""#### Frequently Asked Questions """)
with st.expander("What are behavioral screen, professional screen and resume screen?"):
    st.write("""
    The behavioral screen evaluates how the candidate handles workplace situations, while the resume screen assesses their past experience and the professional screen evaluates their qualifications and necessary skills.
    """)
with st.expander("Why use AI Interviewer instead of ChatGPT?"):
    st.write("""Though AI Interviewer is powered OpenAI API, we aim to provide high-quality interview questions as close as possible to your submitted job
    descriptions / resume. It also elimates the need to find/write high quality prompt every time to configure ChatGPT.""")
with st.expander("How do I start a new interview session?"):
    st.write("""
    Just refresh the page! Without refreshing the page, streamlit will keep the previous session.
    """)
with st.expander("Is AI Interviewer realiable?"):
    st.write("""AI Interviewer is absolutely a reliable tool to practice your interview skills!
    However, we are aware generative AI is not perfect. Sometimes, the questions generated by AI Interviewer may not be very relevant to your job descriptions,
    and the sample answers may not be accurate. Our goal is to minimize the error rate of AI Interviewer, and we are working on it!""")
with st.expander("Is my information secure when using AI Interviewer?"):
    st.write("""Yes! We do not store any of your information. """)
with st.expander("Will AI Interviewer be powered by GPT-4 or any other LLM models?"):
    st.write("""Yes! We're working on it!""")
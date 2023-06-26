import streamlit as st
import json
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from PIL import Image

st.spinner(text="loading...")

def load_lottiefile(filepath: str):
    with open(filepath, "r") as f:
        return json.load(f)

im = Image.open("static/images/chat.png")
st.set_page_config(page_title = "GPTInterviewer", page_icon = im, layout = "wide")

with st.sidebar:

    st.markdown('### GPTInterviewer - V0.1.1')
    st.markdown("""  
    
    #### What's Next? 
    
    v0.1.2: 
    1. A more robust llm-powered evaluation system.
    We're trying to build a system that are close to human evaluation in real world.
    
    #### Powered by
    
    [OpenAI](https://openai.com/)
    
    [FAISS](https://github.com/facebookresearch/faiss)
    
    [Langchain](https://github.com/hwchase17/langchain)
    
    #### Addition
    We're trying to access GPT-4 for everyone to use.
    
    Feel free to contact us if you have any questions or suggestions.
    
    (Email: zwang531@fordham.edu)
    
                """)

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Your Career Workshop Anytime from Anywhere</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'> GPT Interviewer is a generative AI powered tool that provides you with realistic interview experience</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'> You're no longer practice with a static list of questions.</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.write(' ')
with col2:
    st_lottie(load_lottiefile("images/talk.json"), speed=1, reverse=False, loop=True, quality="high")
with col3:
    st.write(' ')

selected = option_menu(
        menu_title= None,
        options=["Resume Screen", "Technical Screen", "Behavioral Screen"],
        icons = ["cloud-upload", "cast", "cast"],
        default_index=0,
        orientation="horizontal",
    )

st.markdown("#")
st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Features</h1>", unsafe_allow_html=True)
st.markdown("#")
col1, col2, col3 = st.columns(3)
with col1:
    st_lottie(load_lottiefile("images/brain.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
    st.markdown("<h3 style='text-align: center;'>Personalization</h3>", unsafe_allow_html=True)
with col2:
    st_lottie(load_lottiefile("images/recording.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
    st.markdown("<h3 style='text-align: center;'>Voice Interaction</h3>", unsafe_allow_html=True)
with col3:
    st_lottie(load_lottiefile("images/evaluation.json"), speed=1, reverse=False, loop=True, quality="high", height=300)
    st.markdown("<h3 style='text-align: center;'>Feedback</h3>", unsafe_allow_html=True)


st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'> Contact: zwang531@fordham.edu </p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: grey;'> Fordham University Center of Digital Transformation DesignLAB </p>", unsafe_allow_html=True)
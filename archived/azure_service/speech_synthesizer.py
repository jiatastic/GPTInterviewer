import streamlit as st
import azure.cognitiveservices.speech as speechsdk
def speech_synthesizer(text):

    speech_key, service_region = st.secrets["SPEECH_KEY"], st.secrets["SPEECH_REGION"]
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)

    speech_config.speech_synthesis_voice_name = 'en-US-JennyMultilingualNeural'

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    result = speech_synthesizer.speak_text_async(text).get()

    return result

import streamlit as st
import websockets
import asyncio
import base64
import json
import pyaudio
import os
from pathlib import Path

# Session state
if 'text' not in st.session_state:
    st.session_state['text'] = 'Listening...'
    st.session_state['run'] = False

# Audio parameters
st.sidebar.header('Audio Parameters')

FRAMES_PER_BUFFER = int(st.sidebar.text_input('Frames per buffer', 3200))
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = int(st.sidebar.text_input('Rate', 16000))
p = pyaudio.PyAudio()

# Open an audio stream with above parameter settings
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES_PER_BUFFER
)


# Start/stop audio transmission
def start_listening():
    st.session_state['run'] = True


def download_transcription():
    read_txt = open('transcription.txt', 'r')
    st.download_button(
        label="Download transcription",
        data=read_txt,
        file_name='transcription_output.txt',
        mime='text/plain')


def stop_listening():
    st.session_state['run'] = False


# Web user interface
st.title('🎙️ Real-Time Transcription App')

with st.expander('About this App'):
    st.markdown('''
	This Streamlit app uses the AssemblyAI API to perform real-time transcription.

	Libraries used:
	- `streamlit` - web framework
	- `pyaudio` - a Python library providing bindings to [PortAudio](http://www.portaudio.com/) (cross-platform audio processing library)
	- `websockets` - allows interaction with the API
	- `asyncio` - allows concurrent input/output processing
	- `base64` - encode/decode audio data
	- `json` - allows reading of AssemblyAI audio output in JSON format
	''')

col1, col2 = st.columns(2)

col1.button('Start', on_click=start_listening)
col2.button('Stop', on_click=stop_listening)


# Send audio (Input) / Receive transcription (Output)
async def send_receive():
    URL = f"wss://api.assemblyai.com/v2/realtime/ws?sample_rate={RATE}"

    print(f'Connecting websocket to url ${URL}')

    async with websockets.connect(
            URL,
            extra_headers=(("Authorization", st.secrets['api_key']),),
            ping_interval=5,
            ping_timeout=20
    ) as _ws:

        r = await asyncio.sleep(0.1)
        print("Receiving messages ...")

        session_begins = await _ws.recv()
        print(session_begins)
        print("Sending messages ...")

        async def send():
            while st.session_state['run']:
                try:
                    data = stream.read(FRAMES_PER_BUFFER)
                    data = base64.b64encode(data).decode("utf-8")
                    json_data = json.dumps({"audio_data": str(data)})
                    r = await _ws.send(json_data)

                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

                except Exception as e:
                    print(e)
                    assert False, "Not a websocket 4008 error"

                r = await asyncio.sleep(0.01)

        async def receive():
            while st.session_state['run']:
                try:
                    result_str = await _ws.recv()
                    result = json.loads(result_str)['text']

                    if json.loads(result_str)['message_type'] == 'FinalTranscript':
                        print(result)
                        st.session_state['text'] = result
                        st.write(st.session_state['text'])

                        transcription_txt = open('transcription.txt', 'a')
                        transcription_txt.write(st.session_state['text'])
                        transcription_txt.write(' ')
                        transcription_txt.close()


                except websockets.exceptions.ConnectionClosedError as e:
                    print(e)
                    assert e.code == 4008
                    break

                except Exception as e:
                    print(e)
                    assert False, "Not a websocket 4008 error"

        send_result, receive_result = await asyncio.gather(send(), receive())


asyncio.run(send_receive())

if Path('transcription.txt').is_file():
    st.markdown('### Download')
    download_transcription()
    os.remove('transcription.txt')
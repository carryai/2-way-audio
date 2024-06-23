import asyncio
import logging
from flask import Flask, render_template
import sounddevice as sd
import numpy as np
from scipy.signal import resample
import websockets

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Audio settings
CHANNELS = 1
RATE = 48000
TARGET_RATE = 9600
CHUNK = 512  # Buffer size for low latency
DTYPE = 'int16'  # Use int16 instead of float32

# Find USB audio device
def find_usb_audio_device():
    mic_index = None
    speaker_index = None
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        logging.debug(f"Device {i}: {device['name']}, Input Channels: {device['max_input_channels']}, Output Channels: {device['max_output_channels']}")
        if 'USB' in device['name']:
            if mic_index is None and device['max_input_channels'] > 0:
                mic_index = i
            if speaker_index is None and device['max_output_channels'] > 0:
                speaker_index = i
    return mic_index, speaker_index

mic_index, speaker_index = find_usb_audio_device()

def check_device_availability(index):
    try:
        sd.check_input_settings(device=index, channels=CHANNELS, dtype=DTYPE, samplerate=RATE)
        sd.check_output_settings(device=index, channels=CHANNELS, dtype=DTYPE, samplerate=RATE)
        return True
    except Exception as e:
        logging.error(f"Device {index} not available: {e}")
        return False

def resample_audio(audio_data, original_rate, target_rate):
    number_of_samples = round(len(audio_data) * float(target_rate) / original_rate)
    resampled_audio = resample(audio_data, number_of_samples)
    return resampled_audio.astype(np.int16)

async def audio_stream(websocket, path):
    while True:
        try:
            if not check_device_availability(mic_index) or not check_device_availability(speaker_index):
                logging.warning("Audio device not available. Retrying...")
                continue  # Retry if device is not available

            with sd.Stream(samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=CHUNK, device=(mic_index, speaker_index)) as stream:
                logging.info("Recording...")

                while True:
                    input_data, _ = stream.read(CHUNK)
                    resampled_data = resample_audio(input_data, RATE, TARGET_RATE)
                    await websocket.send(resampled_data.tobytes())
        except Exception as e:
            logging.error(f"Error in handle_audio: {e}")
            break  # Exit the loop if there's an error

@app.route('/')
def index():
    """Audio streaming home page."""
    return render_template('live.html')

if __name__ == "__main__":
    start_server = websockets.serve(audio_stream, '0.0.0.0', 8765)
    asyncio.get_event_loop().run_until_complete(start_server)
    app.run(host='0.0.0.0', threaded=True, port=8080)

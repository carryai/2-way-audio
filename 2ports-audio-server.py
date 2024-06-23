import asyncio
import sounddevice as sd
import websockets
import numpy as np
import queue
import logging
from scipy.signal import resample

# Configuration
SAMPLE_RATE = 48000
CHANNELS = 1
INPUT_PORT = 8081
OUTPUT_PORT = 8080
CHUNK = 8192  # Buffer size
DTYPE = 'int16'  # Use int16f instead of float32


# Set up logging
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')


# Detect USB sound card
def get_usb_sound_card():
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if 'USB' in device['name']:
            return idx
    return None

usb_sound_card = get_usb_sound_card()
if usb_sound_card is None:
    raise ValueError("No USB sound card detected")

def resample_audio(audio_data, original_rate, target_rate):
    number_of_samples = round(len(audio_data) * float(target_rate) / original_rate)
    resampled_audio = resample(audio_data, number_of_samples)
    return resampled_audio.astype(np.int16)

# Queue for audio data
audio_queue = queue.Queue()

# WebSocket server to send microphone audio
async def send_audio(websocket, path):
    logging.debug("Client connected to send audio")

    async def audio_sender():
        while True:
            audio_data = await loop.run_in_executor(None, audio_queue.get)
            if audio_data:
                # logging.debug(f"Sending audio data: {len(audio_data)} bytes")
                await websocket.send(audio_data)
                

    loop = asyncio.get_event_loop()
    sender_task = asyncio.ensure_future(audio_sender())

    def callback(indata, frames, time, status):
        #if status:
            # logging.warning(f"Sound device status: {status}")
        audio_queue.put(indata.tobytes())
        # logging.debug(f"Audio data put in queue: {len(indata.tobytes())} bytes")

    try:
        with sd.Stream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE, blocksize=CHUNK, device=usb_sound_card) as stream:
            while True:
                input_data, _ = stream.read(CHUNK)

                # Resample the audio data from 48000 Hz to 9600 Hz for sending
                #input_data_resampled = resample_audio(input_data, 48000, 9600)

                if websocket.open:
                    await websocket.send(input_data.tobytes())
                                    
            await websocket.wait_closed()
    except Exception as e:
        logging.error(f"Error in InputStream: {e}")
    finally:
        sender_task.cancel()
        logging.debug("Client disconnected from send audio")

# WebSocket server to receive and play audio
async def receive_audio(websocket, path):
    logging.debug("Client connected to receive audio")
    async for message in websocket:
        audio_data = np.frombuffer(message, dtype=np.int16)
        # logging.debug(f"Received audio data: {len(message)} bytes")
        try:
            sd.play(audio_data, samplerate=SAMPLE_RATE, device=usb_sound_card)
            sd.wait()
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
    logging.debug("Client disconnected from receive audio")

async def main():
    send_server = await websockets.serve(send_audio, "localhost", INPUT_PORT)
    receive_server = await websockets.serve(receive_audio, "localhost", OUTPUT_PORT)
    logging.info(f"Server started on ports {INPUT_PORT} (send) and {OUTPUT_PORT} (receive)")

    await asyncio.gather(send_server.wait_closed(), receive_server.wait_closed())

if __name__ == "__main__":
    asyncio.run(main())

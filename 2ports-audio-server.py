import asyncio
import sounddevice as sd
import websockets
import numpy as np

# Configuration
SAMPLE_RATE = 48000
CHANNELS = 1
BUFFER_SIZE = 1024
INPUT_PORT = 8080
OUTPUT_PORT = 8081

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

# WebSocket server to send microphone audio
async def send_audio(websocket, path):
    def callback(indata, frames, time, status):
        if status:
            print(status)
        audio_data = indata.tobytes()
        asyncio.run_coroutine_threadsafe(websocket.send(audio_data), asyncio.get_event_loop())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, device=usb_sound_card, callback=callback):
        await websocket.wait_closed()

# WebSocket server to receive and play audio
async def receive_audio(websocket, path):
    async for message in websocket:
        audio_data = np.frombuffer(message, dtype=np.float32)
        sd.play(audio_data, samplerate=SAMPLE_RATE, device=usb_sound_card)
        sd.wait()

async def main():
    send_server = websockets.serve(send_audio, "localhost", INPUT_PORT)
    receive_server = websockets.serve(receive_audio, "localhost", OUTPUT_PORT)

    await asyncio.gather(send_server, receive_server)

if __name__ == "__main__":
    asyncio.run(main())

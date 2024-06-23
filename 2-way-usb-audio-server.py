import asyncio
import websockets
import sounddevice as sd
import numpy as np
import time


# Audio settings
CHANNELS = 1
RATE = 48000
CHUNK = 4000  # Buffer size
DTYPE = 'int16'  # Use int16f instead of float32

# Global variable to store the current active websocket
current_websocket = None
current_websocket_lock = asyncio.Lock()

# Find USB audio device
def find_usb_audio_device():
    mic_index = None
    speaker_index = None
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"Device {i}: {device['name']}, Input Channels: {device['max_input_channels']}, Output Channels: {device['max_output_channels']}")
        if 'USB' in device['name']:
            if mic_index is None and device['max_input_channels'] > 0:
                mic_index = i
            if speaker_index is None and device['max_output_channels'] > 0:
                speaker_index = i
    return mic_index, speaker_index

mic_index, speaker_index = find_usb_audio_device()

# Manually set device indices if automatic detection fails
# mic_index = 1  # Set this to the correct index for your microphone
# speaker_index = 2  # Set this to the correct index for your speakers

def check_device_availability(index):
    try:
        sd.check_input_settings(device=index, channels=CHANNELS, dtype=DTYPE, samplerate=RATE)
        sd.check_output_settings(device=index, channels=CHANNELS, dtype=DTYPE, samplerate=RATE)
        return True
    except Exception as e:
        print(f"Device {index} not available: {e}")
        return False

async def handle_audio(websocket):
    try:
        with sd.Stream(samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=0,
                       device=(mic_index, speaker_index), latency="low") as stream:
            while True:
                # Read audio input
                input_data, _ = stream.read(4000)
                if websocket.open:
                    await websocket.send(input_data.tobytes())
                    # print("Sent audio data")

                # Receive audio output
                data = await websocket.recv()
                if data:
                    audio_data = np.frombuffer(data, dtype=DTYPE)
                    #print(f"Received audio data of length: {len(audio_data)}")
                    stream.write(audio_data)

    except websockets.ConnectionClosed:
        print("WebSocket connection closed")
    except Exception as e:
        print(f"Error in handle_audio: {e}")

async def audio_handler(websocket, path):
    global current_websocket

    async with current_websocket_lock:
        if current_websocket is not None:
            try:
                await current_websocket.send("disconnect")
                await current_websocket.close()
                print("Disconnected previous client")
            except Exception as e:
                print(f"Error disconnecting previous client: {e}")

            # Wait for 1 second before allowing a new connection
            await asyncio.sleep(1)

        current_websocket = websocket

    await handle_audio(websocket)

async def main():
    if mic_index is None or speaker_index is None:
        print("Error: Could not find USB audio device.")
    elif not check_device_availability(mic_index) or not check_device_availability(speaker_index):
        print("Error: One or more audio devices are not available.")
    else:
        print(f"Using microphone device index: {mic_index}")
        print(f"Using speaker device index: {speaker_index}")
        async with websockets.serve(audio_handler, '0.0.0.0', 8080):
            print("Server started at http://0.0.0.0:8080/")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

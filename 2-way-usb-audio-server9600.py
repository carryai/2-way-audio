import asyncio
import websockets
import sounddevice as sd
import numpy as np
from scipy.signal import resample

# Audio settings
CHANNELS = 1
RATE = 48000
TARGET_RATE = 9600
CHUNK = 1024  # Buffer size
DTYPE = 'int16'  # Use int16 instead of float32

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

def resample_audio(audio_data, original_rate, target_rate):
    number_of_samples = round(len(audio_data) * float(target_rate) / original_rate)
    resampled_audio = resample(audio_data, number_of_samples)
    return resampled_audio.astype(np.int16)

async def handle_audio(websocket):
    try:
        with sd.Stream(samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=CHUNK,
                       device=(mic_index, speaker_index)) as stream:
            while True:
                # Read audio input
                input_data, _ = stream.read(CHUNK)
                
                # Resample the audio data from 48000 Hz to 9600 Hz for sending
                input_data_resampled = resample_audio(input_data, RATE, TARGET_RATE)

                if websocket.open:
                    await websocket.send(input_data_resampled.tobytes())
                    # print("Sent audio data")

                # Receive audio output
                data = await websocket.recv()
                if data:
                    audio_data = np.frombuffer(data, dtype=DTYPE)
                    print(f"Received audio data of length: {len(audio_data)}")
                    
                    # Resample the received audio data from 9600 Hz to 48000 Hz for playback
                    output_data_resampled = resample_audio(audio_data, TARGET_RATE, RATE)
                    stream.write(output_data_resampled)

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

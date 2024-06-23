import asyncio
import websockets
import sounddevice as sd
import numpy as np
import queue

# Audio settings
CHANNELS = 1
RATE = 48000
CHUNK = 4096  # Buffer size
DTYPE = 'int16'  # Use int16 instead of float32

# Global variables
current_websocket = None
current_websocket_lock = asyncio.Lock()
audio_queue = queue.Queue()



# Find USB audio device
def find_usb_audio_device():
    mic_index = None
    speaker_index = None
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if 'USB' in device['name']:
            print(f"Device {i}: {device['name']}, Input Channels: {device['max_input_channels']}, Output Channels: {device['max_output_channels']}")
                        
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
        print(f"Device {index} not available: {e}")
        return False

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Audio callback status: {status}")
    audio_queue.put(indata.copy())
    #print(f"Audio data added to queue: {indata.shape}")

async def handle_audio_output(websocket, output_stream):
    try:
        while websocket.open:
            data = await websocket.recv()
            if data:
                audio_data = np.frombuffer(data, dtype=DTYPE)
                print(f"Received audio data of length: {len(audio_data)} :: {audio_data.any()}")
                # Ensure audio_data is proper in length and not empty
                if audio_data.any():
                    output_stream.write(audio_data)
                    #print (audio_data)
                    #output_stream.write( audio_signal )
                    # Write the audio signal in chunks
                  
                else:
                    print("Invalid audio data received, skipping...")

    except websockets.ConnectionClosed:

        while not audio_queue.empty():
            audio_queue.get()
                    
        print("WebSocket connection closed")
    except Exception as e:
        print(f"Error in handle_audio_output: {e}")

async def audio_handler(websocket, path):
    global current_websocket

    async with current_websocket_lock:
        if current_websocket is not None:
            try:
                await current_websocket.send("disconnect")
                await current_websocket.close()
                print("Disconnected previous client")

                while not audio_queue.empty():
                    audio_queue.get()

            except Exception as e:
                print(f"Error disconnecting previous client: {e}")

            # Wait for 1 second before allowing a new connection
            await asyncio.sleep(1)

        current_websocket = websocket

    # Open the output stream for the duration of the WebSocket connection
    with sd.OutputStream(samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=CHUNK, device=speaker_index) as output_stream:
        await handle_audio_output(websocket, output_stream)

async def stream_audio():
    with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=DTYPE, blocksize=CHUNK, device=mic_index, callback=audio_callback, dither_off=True, latency='low', clip_off=True, prime_output_buffers_using_stream_callback=False):
        while True:

            #print( audio_queue.empty())

            if not audio_queue.empty():
                data = audio_queue.get()
                #print(f"Sending audio data of length: {len(data)}")
                async with current_websocket_lock:
                    if current_websocket and current_websocket.open:
                        # Use asyncio.create_task to send data without blocking
                        asyncio.create_task(current_websocket.send(data.tobytes()))

            # Clear the queue periodically to avoid excessive delay
            if audio_queue.qsize() > 1:  # Adjust the threshold as necessary
                print("Clearing audio queue to avoid delay")
                while not audio_queue.empty():
                    audio_queue.get()

            await asyncio.sleep(0.001)  # Adjust sleep time as necessary

async def main():
    if mic_index is None or speaker_index is None:
        print("Error: Could not find USB audio device.")
    elif not check_device_availability(mic_index) or not check_device_availability(speaker_index):
        print("Error: One or more audio devices are not available.")
    else:
        print(f"Using microphone device index: {mic_index}")
        print(f"Using speaker device index: {speaker_index}")

        # Start the audio streaming task
        asyncio.create_task(stream_audio())

        # Start the WebSocket server
        async with websockets.serve(audio_handler, '0.0.0.0', 8080):
            print("Server started at http://0.0.0.0:8080/")
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())

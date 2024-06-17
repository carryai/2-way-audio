# pactl set-sink-volume @DEFAULT_SINK@ 80%
# amixer -D pulse sset Master 50%
# sudo apt-get install portaudio19-dev

# https://audio.carryai.co/
import asyncio
import numpy as np
import sounddevice as sd
import websockets

audio_config = {
    'samplerate': 48000,
    'device_index': None,
}

devices = sd.query_devices()
for i, device in enumerate(devices):
    if 'USB' in device['name']:
        print(f'Setting default device to {device["name"]}')
        audio_config['device_index'] = i
        break
if audio_config['device_index'] is None:
    print('No USB soundcard found')
    exit()

stream = sd.OutputStream(channels=1, dtype='float32', samplerate=audio_config['samplerate'], device=audio_config['device_index'])

active_websocket = None

async def audio_server(websocket, _):
    global active_websocket

    # Check if there is a currently active connection that isn't the same as the new one
    if active_websocket and active_websocket != websocket:
        # Notify the existing connection before closing it
        await active_websocket.send("Your stream has been replaced by a new connection.")
        await active_websocket.close()
        print("Closed the older connection to accommodate the new one.")
        # Stop the stream to flush the buffer
        if stream.active:
            stream.stop()
            print("Stream stopped to flush audio buffer.")


    active_websocket = websocket
    print(f"New active connection: {websocket}")

    try:
        stream.start()  # Restart the stream with the new connection
        print("Stream started for new connection.")
        async for message in websocket:
            audio_data = np.frombuffer(message, dtype=np.float32)
            stream.write(audio_data)
    except Exception as e:
        print(f"Error processing audio: {e}")
    finally:
        if websocket == active_websocket:
            if stream.active:
                stream.stop()
                print("Stream stopped as the connection is closing.")
            active_websocket = None
            print("Active connection has been reset.")


async def main():
    async with websockets.serve(audio_server, '0.0.0.0', 8080):
        print("Server started at http://0.0.0.0:8080/")
        await asyncio.Future()  # Run forever

if __name__ == '__main__':
    asyncio.run(main())

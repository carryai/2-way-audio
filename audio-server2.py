import asyncio
import websockets
import sounddevice as sd
import numpy as np

connected_client = None
audio_queue = asyncio.Queue()

async def audio_stream(websocket, path):
    global connected_client
    if connected_client:
        await connected_client.close(reason="New connection established")
    connected_client = websocket

    async def send_audio():
        while True:
            indata = await audio_queue.get()
            await websocket.send(indata.tobytes())

    async def receive_audio():
        while True:
            try:
                data = await websocket.recv()
                audio_data = np.frombuffer(data, dtype=np.int16)
                sd.play(audio_data, samplerate=48000)
            except websockets.ConnectionClosed:
                break

    send_task = asyncio.create_task(send_audio())
    receive_task = asyncio.create_task(receive_audio())

    await asyncio.gather(send_task, receive_task)

def audio_callback(indata, frames, time, status):
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(asyncio.create_task, audio_queue.put(indata.copy()))

async def main():
    async with websockets.serve(audio_stream, "localhost", 8765):
        with sd.InputStream(callback=audio_callback, channels=1, samplerate=48000):
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

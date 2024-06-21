"""
Extraction of javascript functions from 2way-audio.html to a python script.
"""
import asyncio
import websockets
import numpy as np
import sounddevice as sd

# WebSocket server URL
WS_URL = "ws://192.168.1.20:8080"

# Audio settings
RATE = 48000
CHUNK = 2048


class WebSocketAudioClient:
    def __init__(self):
        self.websocket = None
        self.gain = 1.0
        self.audio_buffer_queue = []
        self.loop = None
        self.stream = None

    async def connect_websocket(self):
        try:
            print(f"Attempting to connect to {WS_URL}")
            self.websocket = await websockets.connect(WS_URL, open_timeout=10)
            print("Status: Connected")
            await asyncio.gather(self.start_audio(), self.receive_audio())
        except Exception as e:
            print(f"Connection failed: {e}")

    async def disconnect_websocket(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        print("Status: Disconnected")
        self.stop_audio()

    async def start_audio(self):
        self.stream = sd.Stream(
            samplerate=RATE,
            blocksize=CHUNK,
            dtype="int16",
            channels=1,
            callback=self.audio_callback,
        )
        self.stream.start()

    def stop_audio(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def audio_callback(self, in_data, out_data, frames, time, status):
        if status:
            print(f"Status: {status}")

        audio_data = np.frombuffer(in_data, dtype=np.int16)
        audio_data = np.int16(audio_data * self.gain)

        if self.websocket:
            future = asyncio.run_coroutine_threadsafe(
                self.send_audio(audio_data.tobytes()), self.loop
            )
            try:
                future.result()  # Wait for the coroutine to complete
            except Exception as e:
                print(f"Exception in audio_callback: {e}")

        if self.audio_buffer_queue:
            out_data[:] = np.array(
                self.audio_buffer_queue.pop(0), dtype=np.int16
            ).reshape(out_data.shape)
        else:
            out_data.fill(0)

    async def send_audio(self, audio_data):
        try:
            await self.websocket.send(audio_data)
        except websockets.ConnectionClosed:
            print("Connection closed while sending audio data")

    async def receive_audio(self):
        try:
            async for message in self.websocket:
                self.audio_buffer_queue.append(np.frombuffer(message, dtype=np.int16))
        except websockets.ConnectionClosed:
            print("Connection closed while receiving audio data")

    async def run(self):
        self.loop = asyncio.get_running_loop()
        await self.connect_websocket()


if __name__ == "__main__":
    asyncio.run(WebSocketAudioClient().run())

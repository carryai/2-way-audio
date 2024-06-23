import sounddevice as sd
import numpy  as np

# Audio settings
RATE = 48000
DURATION = 5  # in seconds
FREQUENCY = 440  # in Hz (A4 note)
DTYPE = 'int16'
CHUNK_SIZE = 4096  # Buffer size


# Generate a sine wave
t = np.linspace(0, DURATION, int(RATE * DURATION), endpoint=False)
audio_signal = (0.5 * np.sin(2 * np.pi * FREQUENCY * t) * (2**15 - 1)).astype(DTYPE)

print(f"Generated audio signal of length: {len(audio_signal)}")

# Set default device if you want to utilize some specific sound device
# sd.default.device = 'your-device-name-or-index-here'

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


if speaker_index is not None:
    print (speaker_index)
    try:
        with sd.OutputStream(samplerate=RATE, channels=1, dtype=DTYPE, blocksize=CHUNK_SIZE, device=speaker_index) as output_stream:
            # Write the audio signal in chunks
            output_stream.write(audio_signal)
            
            # for start in range(0, len(audio_signal), CHUNK_SIZE):
            #     end = start + CHUNK_SIZE
            #     output_stream.write(audio_signal[start:end])
        print("Audio playback finished successfully.")
    except Exception as e:
        print(f"An error occurred during audio playback: {e}")
else:
    print("No available output device found.")

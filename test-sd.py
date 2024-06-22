import sounddevice as sd
import numpy  as np

# Set parameters
fs = 48000    # Sample rate
f = 440       # Frequency for A4 note
duration = 5  # Duration in seconds

# Generate time axis
t = np.arange(fs * duration) / fs

# Generate audio data
a = 0.2 * np.sin(2 * np.pi * f * t)

# Set default device if you want to utilize some specific sound device
# sd.default.device = 'your-device-name-or-index-here'

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


sd.default.device = speaker_index
# Play audio 
sd.play(a, fs)

# Wait until audio is done playing
sd.wait()

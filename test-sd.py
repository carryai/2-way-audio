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

sd.default.device = 24
# Play audio 
sd.play(a, fs)

# Wait until audio is done playing
sd.wait()

import sounddevice as sd

devices = sd.query_devices()  # query all available devices
for i, device in enumerate(devices):
    print(i, device['name'])  # print devices
    if 'usb' in device['name'].lower():
        print(f'Setting default device to {device["name"]}')
        print('USB device rates:', device['default_samplerate'], device['default_low_output_latency'], device['default_high_output_latency'])

        sd.default.device = i   # set the device with index 'i' as the default device
        break

#sd.default.device = 'USB Soundcard Name'  # replace with your soundcard name
    
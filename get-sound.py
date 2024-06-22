import sounddevice as sd



#sd.default.device = 'USB Soundcard Name'  # replace with your soundcard name
    

def print_device_info():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"Device {i}: {device['name']}")
        print(f"  Max Input Channels: {device['max_input_channels']}")
        print(f"  Max Output Channels: {device['max_output_channels']}")
        print(f"  Default Sample Rate: {device['default_samplerate']}\n")

def check_supported_sample_rates(device_index):
    sample_rates = [8000, 16000, 22050, 32000, 44100, 48000, 96000, 192000]
    supported_sample_rates = []

    for rate in sample_rates:
        try:
            sd.check_input_settings(device=device_index, samplerate=rate)
            supported_sample_rates.append(rate)
        except Exception as e:
            pass
    
    return supported_sample_rates

def main():

    devices = sd.query_devices()  # query all available devices
    for i, device in enumerate(devices):
        print(i, device['name'])  # print devices
        if 'usb' in device['name'].lower():
            print(f'Setting default device to {device["name"]}')
            print('USB device rates:', device['default_samplerate'], device['default_low_output_latency'], device['default_high_output_latency'])

            sd.default.device = i   # set the device with index 'i' as the default device
            break

    print_device_info()

    device_index = int(input("Enter the device index to check supported sample rates: "))
    supported_sample_rates = check_supported_sample_rates(device_index)
    print(f"Supported sample rates for device {device_index}: {supported_sample_rates}")

if __name__ == "__main__":
    main()

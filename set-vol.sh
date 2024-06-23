#!/bin/bash

# Set the master volume to 100%
# amixer set Master 100%
# amixer -c 1 set Master 100%
# amixer -c 1 set 'PCM' 100%
# amixer set Master 100% unmute

sudo apt install alsa-utils -y

# Get the USB audio device card number
usb_card=$(aplay -l | grep -i 'usb' | awk -F '[ :]' '{print $2}' | head -n 1)

# Check if a USB audio device was found
if [ -z "$usb_card" ]; then
  echo "No USB audio device found"
  exit 1
fi

amixer -c "$usb_card" 

# Set the master volume to 100% and unmute for the USB audio card
amixer -c "$usb_card" set Master 100% unmute
amixer -c "$usb_card" set 'PCM' 100% unmute
amixer -c "$usb_card" set 'PCM' 100% unmute

# Check if USB capture device was found
if [ -z "$usb_card" ]; then
  echo "No USB capture device found"
else
  # Set the capture volume to 100% and unmute for the USB capture card
  amixer -c "$usb_capture_card" set Capture 100% cap
  echo "Capture volume set to 100% and unmuted for USB audio device (card $usb_capture_card)"
fi
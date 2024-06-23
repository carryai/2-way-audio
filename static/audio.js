document.addEventListener("DOMContentLoaded", function () {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const audioElement = document.getElementById('audio');
    const scriptNode = audioContext.createScriptProcessor(512, 1, 1);
    const startButton = document.getElementById('startButton');

    scriptNode.onaudioprocess = function (audioProcessingEvent) {
        const inputBuffer = audioProcessingEvent.inputBuffer;
        const outputBuffer = audioProcessingEvent.outputBuffer;

        for (let channel = 0; channel < outputBuffer.numberOfChannels; channel++) {
            const inputData = inputBuffer.getChannelData(channel);
            const outputData = outputBuffer.getChannelData(channel);

            for (let sample = 0; sample < inputBuffer.length; sample++) {
                outputData[sample] = inputData[sample];
            }
        }
    };

    const source = audioContext.createMediaElementSource(audioElement);
    source.connect(scriptNode);
    scriptNode.connect(audioContext.destination);

    startButton.addEventListener('click', function () {
        fetchAudioStream();
        audioElement.play();
    });

    function fetchAudioStream() {
        fetch('/audio')
            .then(response => {
                const reader = response.body.getReader();
                const read = () => {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            return;
                        }
                        const audioBlob = new Blob([value], { type: 'audio/x-wav' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        audioElement.src = audioUrl;
                        audioElement.play();
                        read();
                    });
                };
                read();
            });
    }
});

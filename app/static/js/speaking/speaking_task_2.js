document.addEventListener("DOMContentLoaded", function () {
    const prepButton = document.getElementById('start-preparation');
    const startButton = document.getElementById('start-recording');
    const submitButton = document.getElementById('submit-btn');
    const countdownTimer = document.getElementById('countdown-text');
    const mimeType = 'audio/webm;codecs=opus';
    let recorder;
    let chunks = [];
    let countdownInterval;
    let recordedBlob = null;  // ✅ Store the recorded blob globally

    // Start 1-minute preparation countdown
    prepButton.addEventListener('click', function () {
        let prepTimeLeft = 60;
        countdownTimer.innerText = prepTimeLeft;
        countdownInterval = setInterval(() => {
            prepTimeLeft--;
            countdownTimer.innerText = prepTimeLeft;

            if (prepTimeLeft <= 0) {
                clearInterval(countdownInterval);
                prepButton.classList.add("d-none");
                startButton.classList.remove("d-none");
                countdownTimer.innerText = "120";
            }
        }, 1000);
    });

    // Start 2-minute speaking countdown when recording begins
    startButton.addEventListener('click', function () {
        submitButton.classList.remove("d-none"); 
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                chunks = [];
                recorder = new MediaRecorder(stream, { mimeType: mimeType });

                recorder.ondataavailable = event => chunks.push(event.data);

                recorder.onstop = () => {
                    console.log('✅ Recording stopped, saving blob...');
                    
                    if (chunks.length === 0) {
                        console.error("🚨 No audio chunks captured!");
                        alert("Recording failed, please try again.");
                        return;
                    }
                
                    recordedBlob = new Blob(chunks, { type: mimeType });
                    chunks = [];  // ✅ Clear chunks after saving
                
                    console.log("🎤 Recorded blob saved:", recordedBlob);
                    submitButton.classList.remove("d-none");
                    submitButton.disabled = false;
                };
                
                
                recorder.start();
                startButton.disabled = true;

                let timeLeft = 120;
                countdownTimer.innerText = timeLeft;
                countdownInterval = setInterval(() => {
                    timeLeft--;
                    countdownTimer.innerText = timeLeft;

                    if (timeLeft <= 0) {
                        clearInterval(countdownInterval);
                        recorder.stop();
                    }
                }, 1000);
            })
            .catch(err => console.error('Error accessing microphone:', err));
    });

    // ✅ Ensure recording stops before submission
    submitButton.addEventListener("click", function (event) {
        event.preventDefault();

        if (recorder && recorder.state === "recording") {
            console.log("⏹️ Stopping recording before submission...");
            clearInterval(countdownInterval);
            recorder.stop();
        }

        setTimeout(() => {
            if (!recordedBlob) {
                alert("No recording found! Please try recording again.");
                console.error("🚨 No recordedBlob found!");
                return;
            }

            console.log("✅ Recording found, preparing submission...");
        
            const formData = new FormData();
            formData.append('question_number', document.querySelector("input[name='question_number']").value);
            formData.append('audio_file', recordedBlob, 'audio_record.webm');
        
            submitButton.disabled = true;
            submitButton.innerText = "Submitting...";
        
            fetch('/speaking/speaking_task_2_submit', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(data => {
                console.log("✅ Server response:", data);
                window.location.href = `/speaking/speaking_task_2_feedback?question_number=${document.querySelector("input[name='question_number']").value}`;
            })
            .catch(err => console.error('❌ Error uploading file:', err));
        }, 500);  // ✅ Small delay to ensure blob is set
    });
}); 
import React from 'react';
import ReactDOM from 'react-dom/client';
import { GoogleOAuthProvider } from '@react-oauth/google';
import './index.css';
import App from './App';
// import reportWebVitals from './reportWebVitals';
const GOOGLE_CLIENT_ID = "672355153898-3opoqa4ud89lp2kboajbibbhfvep8mmd.apps.googleusercontent.com"

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <App />
    </GoogleOAuthProvider>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals

const startRecording = () => {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const recorder = new MediaRecorder(stream);
                mediaRecorder.current = recorder;
                audioChunks.current = [];
                recorder.start();
                setIsRecording(true);
                recorder.onstop = () => {
                    setIsTranscribing(true);
                    const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
                    const formData = new FormData();
                    formData.append('audio', audioBlob);
                    formData.append('language', globalLanguage);

                    fetch('http://localhost:8000/api/transcribe/', {
                        method: 'POST',
                        body: formData,
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        setInput(data.text);
                        handleSendMessage(data.text);
                    })
                    .catch(err => {
                        console.error("Error during transcription:", err);
                        setInput("Sorry, I couldn't understand that. Please try again.");
                    })
                    .finally(() => {
                        setIsTranscribing(false);
                    });
                    
                    stream.getTracks().forEach(track => track.stop());
                };
                recorder.ondataavailable = event => {
                    audioChunks.current.push(event.data);
                };
            })
            .catch(err => {
                console.error("Error accessing microphone:", err);
                alert("Microphone access was denied. Please allow microphone access in your browser settings.");
            });
    };

    const stopRecording = () => {
        if (mediaRecorder.current && mediaRecorder.current.state === "recording") {
            mediaRecorder.current.stop();
        }
        setIsRecording(false);
    };

    const handleAudioClick = () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    };
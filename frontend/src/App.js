// src/App.js

import React, { useState, useRef } from 'react';
import './App.css';
import ChatInterface from './components/ChatInterface';
import InputArea from './components/InputArea';
import OnScreenKeyboard from './components/OnScreenKeyboard';
import LanguageSelector from './components/LanguageSelector'; // Import the new component
import { translations } from './translations'; // Import the translations

function App() {
  const [messages, setMessages] = useState([]);
  const [showKeyboard, setShowKeyboard] = useState(false);
  const [input, setInput] = useState('');
  const [isChatActive, setIsChatActive] = useState(false);
  const [globalLanguage, setGlobalLanguage] = useState('en');
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorder = useRef(null); 
  const audioChunks = useRef([]);

  const startRecording = () => {
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        const recorder = new MediaRecorder(stream);
        mediaRecorder.current = recorder;
        audioChunks.current = []; // Clear previous recording chunks

        recorder.ondataavailable = event => {
          audioChunks.current.push(event.data);
        };

         recorder.onstop = () => {
          const audioBlob = new Blob(audioChunks.current, { type: 'audio/webm' });
          const languageCode = translations[globalLanguage].languageCode; // Get the correct language code!
          
          // --- REAL IMPLEMENTATION (replaces the old simulation) ---
          
          // 1. Create FormData to send both the file and the language code
          const formData = new FormData();
          formData.append('audioFile', audioBlob);
          formData.append('language', languageCode);

          console.log(`Preparing to send audio for transcription in language: ${languageCode}`);

          // 2. Use 'fetch' to send the data to your backend endpoint
          // (This endpoint '/api/transcribe' is hypothetical and needs to be created on your server)
          fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
          })
          .then(response => {
            if (!response.ok) {
              throw new Error('Network response was not ok');
            }
            return response.json(); // Expect a JSON response with the text
          })
          .then(data => {
            // 3. Set the input with the transcribed text from the server
            console.log('Transcription received:', data.transcribedText);
            setInput(data.transcribedText);
            if (!isChatActive) setIsChatActive(true);
          })
          .catch(err => {
            console.error("Error during transcription:", err);
            // If transcription fails, notify the user.
            setInput("Sorry, I couldn't understand that. Please try again.");
          });

          // --- END OF REAL IMPLEMENTATION ---
          
          // Clean up the stream tracks
          stream.getTracks().forEach(track => track.stop());
        };

        recorder.start();
        setIsRecording(true);
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

  const handleSendMessage = (text) => {
    if (text.trim() === '') return;

    if (!isChatActive) {
      setIsChatActive(true);
    }

    const newMessages = [...messages, { id: Date.now(), text, sender: 'user' }];
    setMessages(newMessages);
    setInput('');

    setTimeout(() => {
      // Use the translations file for AI responses
      const aiText = messages.length === 0 
        ? translations[globalLanguage].welcomeMessage
        : translations[globalLanguage].sampleResponse;
        
      const aiResponse = { id: Date.now() + 1, text: aiText, sender: 'ai' };
      setMessages(prevMessages => [...prevMessages, aiResponse]);
    }, 1000);
  };

  const handleKeyPress = (key) => {
    if (key === 'Enter') {
      handleSendMessage(input);
    } else if (key === 'Backspace') {
      setInput(input.slice(0, -1));
    } else {
      setInput(input + key);
    }
  };

  const containerClassName = `app-container ${isChatActive ? 'chat-active' : 'chat-inactive'}`;
  const currentTranslation = translations[globalLanguage]; // Get the current language text object

  return (
      <div className={containerClassName}>
        <LanguageSelector setGlobalLanguage={setGlobalLanguage} />
        <main className="main-content">
          <header className="app-header"> 
              <div className="header-content">
                <h1>Agri-Advisor AI</h1> {/* This part is not translated */}
                <p>{currentTranslation.subtitle}</p> {/* Subtitle is translated */}
              </div>
              <LanguageSelector setGlobalLanguage={setGlobalLanguage} />
          </header>
          <div className="input-area-wrapper">
            <InputArea
              input={input}
              setInput={setInput}
              onSendMessage={() => handleSendMessage(input)}
              toggleKeyboard={() => setShowKeyboard(!showKeyboard)}
              placeholderText={currentTranslation.placeholder}
              tooltipAudio={currentTranslation.tooltipAudio}
              tooltipKeyboard={currentTranslation.tooltipKeyboard}
              tooltipSend={currentTranslation.tooltipSend}
              // Pass the new state and handler
              isRecording={isRecording}
              handleAudioClick={handleAudioClick}
            />
          </div>
        </main>
        {showKeyboard && <OnScreenKeyboard onKeyPress={handleKeyPress} />}
        {isChatActive && <ChatInterface messages={messages} />}
      </div>
    );
}

export default App;

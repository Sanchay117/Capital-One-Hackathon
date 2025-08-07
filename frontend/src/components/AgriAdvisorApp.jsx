import React, { useState, useRef, useEffect } from 'react';
import '../App.css'; 
import ChatInterface from './ChatInterface';
import InputArea from './InputArea';
import OnScreenKeyboard from './OnScreenKeyboard';
import LanguageSelector from './LanguageSelector';
import Sidebar from './Sidebar';
import { translations } from '../translations';
import { FiMenu } from 'react-icons/fi';

function AgriAdvisorApp() {
    // --- STATE MANAGEMENT (Unchanged) ---
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef(null);
    const [messages, setMessages] = useState([]);
    const [showKeyboard, setShowKeyboard] = useState(false);
    const [input, setInput] = useState('');
    const [isChatActive, setIsChatActive] = useState(false);
    const [globalLanguage, setGlobalLanguage] = useState('en');
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorder = useRef(null);
    const audioChunks = useRef([]);

    // --- DUMMY DATA (Unchanged) ---
    const dummyChatHistory = [
        { id: 1, title: 'Fertilizer recommendations for wheat' },
        { id: 2, title: 'Best time to plant corn in my area' },
        { id: 3, title: 'How to handle pest infestation' },
        { id: 4, title: 'Crop rotation strategies' },
        { id: 5, title: 'Soil health and nutrient management' },
        { id: 6, title: 'Irrigation techniques for dry seasons' },
        { id: 7, title: 'Market prices for soybeans' },
    ];

    // --- HANDLERS ---
    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    const toggleProfileMenu = () => setIsProfileMenuOpen(!isProfileMenuOpen);
    const handleLogout = () => { alert("Logout functionality would be handled here."); };
    useEffect(() => {
        function handleClickOutside(event) {
            if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
                setIsProfileMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [profileMenuRef]);
    
    const handleKeyPress = (key) => {
        if (key === 'Enter') {
            handleSendMessage(input);
        } else if (key === 'Backspace') {
            setInput(input.slice(0, -1));
        } else {
            setInput(input + key);
        }
    };

    const handleSendMessage = (text) => {
        if (text.trim() === '') return;
        if (!isChatActive) setIsChatActive(true);
        const newTurn = {
            id: Date.now(),
            prompt: text,
            response: `This is a static response to your question about "${text}". In a real application, the AI would provide a detailed, dynamic answer based on your query.`
        };
        setMessages([...messages, newTurn]);
        setInput('');
    };
    
    // --- THE FIX: Re-implementing the Audio Recording Functionality ---

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
                    const languageCode = translations[globalLanguage].languageCode;
                    
                    // --- This is the STATIC implementation ---
                    // It simulates the process without a real backend.
                    console.log(`Simulating transcription for audio blob in language: ${languageCode}`);
                    // In a real app, you would send the audioBlob and languageCode to a server here.
                    
                    setTimeout(() => {
                        // After a delay, set the input to the "couldn't understand" message.
                        setInput("Sorry, I couldn't understand that.");
                    }, 1500); // Simulate a 1.5-second processing delay.
                    
                    // Clean up the stream tracks to turn off the microphone indicator
                    stream.getTracks().forEach(track => track.stop());
                };

                recorder.start();
                setIsRecording(true);
            })
            .catch(err => {
                console.error("Error accessing microphone:", err);
                alert("Microphone access was denied. Please allow microphone access in your browser settings to use this feature.");
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

    // --- End of Audio Functionality ---

    const currentTranslation = translations[globalLanguage];

    // --- RENDER LOGIC (Unchanged) ---
    const renderLandingPage = () => (
        <div className="app-container chat-inactive">
            <main className="main-content">
                <header className="app-header"> 
                    <div className="header-content">
                        <h1>Agri-Advisor AI</h1>
                        <p>{currentTranslation.subtitle}</p>
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
                        isRecording={isRecording}
                        handleAudioClick={handleAudioClick}
                    />
                </div>
            </main>
            {showKeyboard && <OnScreenKeyboard onKeyPress={handleKeyPress} />}
        </div>
    );

    const renderActiveChat = () => (
        <div className="app-container chat-active">
            <header className="app-header"> 
                <div className="header-content">
                    <h1>Agri-Advisor AI</h1>
                </div>
                <LanguageSelector setGlobalLanguage={setGlobalLanguage} />
            </header>
            <ChatInterface messages={messages} />
            <div className="chat-input-section">
                {showKeyboard && <OnScreenKeyboard onKeyPress={handleKeyPress} />}
                <div className="input-area-wrapper">
                    <InputArea
                        input={input}
                        setInput={setInput}
                        onSendMessage={() => handleSendMessage(input)}
                        toggleKeyboard={() => setShowKeyboard(!showKeyboard)}
                        placeholderText={currentTranslation.placeholder}
                        isRecording={isRecording}
                        handleAudioClick={handleAudioClick}
                    />
                </div>
            </div>
        </div>
    );

    return (
        <div className={`app-layout ${isSidebarOpen ? 'sidebar-open' : ''}`}>
            {!isSidebarOpen && (
                <button className="sidebar-open-button" onClick={toggleSidebar}>
                    <FiMenu />
                </button>
            )}

            <Sidebar
                isOpen={isSidebarOpen}
                chatHistory={dummyChatHistory}
                onClose={toggleSidebar}
                onProfileClick={toggleProfileMenu}
                isProfileMenuOpen={isProfileMenuOpen}
                onLogout={handleLogout}
                ref={profileMenuRef}
            />

            <div className="main-content-area">
                {isChatActive ? renderActiveChat() : renderLandingPage()}
            </div>
        </div>
    );
}

export default AgriAdvisorApp;
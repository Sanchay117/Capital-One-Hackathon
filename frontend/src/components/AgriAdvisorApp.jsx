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
    // --- STATE MANAGEMENT ---
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef(null);
    const [messages, setMessages] = useState([]);
    const [showKeyboard, setShowKeyboard] = useState(false);
    const [input, setInput] = useState('');
    const [isChatActive, setIsChatActive] = useState(false);
    const [globalLanguage, setGlobalLanguage] = useState('en');
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false); 
    const [isTyping, setIsTyping] = useState(false);
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

        const turnIndex = messages.length;
        const newUserTurn = { prompt: text, response: null };
        setMessages(prevMessages => [...prevMessages, newUserTurn]);
        
        setInput('');
        setIsTyping(true);

        fetch('http://localhost:8000/api/prompt/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: text,
                language: globalLanguage
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            setMessages(prevMessages => {
                const newMessages = [...prevMessages];
                newMessages[turnIndex].response = data.response;
                return newMessages;
            });
        })
        .catch(err => {
            console.error("Error getting AI response:", err);
            // Update the existing turn with an error message
            setMessages(prevMessages => {
                const newMessages = [...prevMessages];
                newMessages[turnIndex].response = "Sorry, something went wrong. Please try again.";
                return newMessages;
            });
        })
        .finally(() => {
            setIsTyping(false);
        });
    };
    
    // --- AUDIO RECORDING & TRANSCRIPTION IMPLEMENTATION ---
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

    const currentTranslation = translations[globalLanguage];

    // --- RENDER LOGIC ---
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
                        isTranscribing={isTranscribing} // <-- 1. ADD THIS LINE
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
                        isTranscribing={isTranscribing} // <-- 2. ADD THIS LINE
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
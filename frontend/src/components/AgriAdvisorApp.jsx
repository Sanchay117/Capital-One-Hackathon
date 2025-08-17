import React, { useState, useRef, useEffect } from 'react';
import '../App.css'; 
import ChatInterface from './ChatInterface';
import InputArea from './InputArea';
import OnScreenKeyboard from './OnScreenKeyboard';
import LanguageSelector from './LanguageSelector';
import Sidebar from './Sidebar';
import { translations } from '../translations';
import { FiMenu } from 'react-icons/fi';

function AgriAdvisorApp({ onLogout }) {
    // --- STATE MANAGEMENT ---
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef(null);
    const [chatHistory, setChatHistory] = useState([]);
    const [activeChat, setActiveChat] = useState(null);
    const [messages, setMessages] = useState([]);
    const [showKeyboard, setShowKeyboard] = useState(false);
    const [input, setInput] = useState('');
    const [isChatActive, setIsChatActive] = useState(false);
    const [globalLanguage, setGlobalLanguage] = useState(localStorage.getItem('userLanguage') || 'en');
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const mediaRecorder = useRef(null);
    const audioChunks = useRef([]);

    // --- API & DATA HANDLING ---
    const fetchChatHistory = async () => {
        const token = localStorage.getItem('accessToken');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/chats/', {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (response.status === 401) {
                onLogout();
                return null; 
            }
            return await response.json();
        } catch (err) {
            console.error("Failed to fetch chat history:", err);
            return null;
        }
    };

    useEffect(() => {
        const initializeUserSession = async () => {
            const historyData = await fetchChatHistory();
            if (historyData) {
                setChatHistory(historyData);
                if (historyData.length > 0) {
                    await loadChat(historyData[0].id);
                } else {
                    setIsChatActive(false);
                }
            }
        };
        initializeUserSession();
    }, [onLogout]); 

    const handleLanguageChange = async (lang) => {
        const token = localStorage.getItem('accessToken');
        setGlobalLanguage(lang);
        localStorage.setItem('userLanguage', lang);

        try {
            await fetch('http://127.0.0.1:8000/api/profile/language/', {
                method: 'PATCH', 
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ preferred_language: lang }),
            });
        } catch (err) {
            console.error("Failed to save language preference:", err);
        }
    };

    const loadChat = async (chatId) => {
        const token = localStorage.getItem('accessToken');
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/chats/${chatId}/`, {
                headers: { 'Authorization': `Bearer ${token}` },
            });
            if (response.status === 401) { onLogout(); return; }
            const data = await response.json();
            setActiveChat(data);
            const formattedMessages = data.messages.map(msg => ({
                prompt: msg.prompt_text,
                response: msg.response_text
            }));
            setMessages(formattedMessages);
            setIsChatActive(true);
            // THE FIX: Do NOT close the sidebar when loading a chat. The user should control this.
            // setIsSidebarOpen(false); // This line has been removed.
        } catch (err) {
            console.error("Failed to load chat:", err);
        }
    };
    
    const handleSendMessage = async (text) => {
        if (text.trim() === '') return;
        
        const token = localStorage.getItem('accessToken');
        const tempUserTurn = { prompt: text, response: "..." };
        setMessages(prev => [...prev, tempUserTurn]);
        setInput('');
        if (!isChatActive) setIsChatActive(true);
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/messages/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    prompt: text,
                    chat_id: activeChat ? activeChat.id : null,
                    input_type: "text", // This would be dynamic for audio
                    input_language: globalLanguage,
                }),
            });

            if (response.status === 401) { onLogout(); return; }
            const data = await response.json();
            
            setActiveChat(data);
            setMessages(data.messages.map(msg => ({ prompt: msg.prompt_text, response: msg.response_text })));
            
            // After sending a message, refresh the chat history to update the order and title.
            const newHistory = await fetchChatHistory();
            if (newHistory) setChatHistory(newHistory);

        } catch (err) {
            console.error("Error sending message:", err);
            setMessages(prev => prev.slice(0, -1)); // Remove the temp message on error
        }
    };
    
    // --- OTHER HANDLERS ---
    const handleNewChat = () => {
        setIsChatActive(false);
        setMessages([]);
        setActiveChat(null);
        setInput('');
        setIsSidebarOpen(true); // Ensure sidebar is open for a new chat
    };

    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    const toggleProfileMenu = () => setIsProfileMenuOpen(!isProfileMenuOpen);
    
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
        if (key === 'Enter') handleSendMessage(input);
        else if (key === 'Backspace') setInput(input.slice(0, -1));
        else setInput(input + key);
    };
    const handleDeleteChat = async (chatId) => {
        const token = localStorage.getItem('accessToken');
        try {
            const response = await fetch(`http://127.0.0.1:8000/api/chats/${chatId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (response.status === 401) { onLogout(); return; }
            if (!response.ok) { throw new Error('Failed to delete chat.'); }

            setChatHistory(prev => prev.filter(chat => chat.id !== chatId));

            if (activeChat && activeChat.id === chatId) {
                handleNewChat();
            }

        } catch (err) {
            console.error("Error deleting chat:", err);
            alert("Could not delete the chat. Please try again.");
        }
    };
    
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

    const currentTranslation = translations[globalLanguage] || translations.en;

    // --- RENDER LOGIC ---
    const renderLandingPage = () => (
        <div className="app-container chat-inactive">
            <main className="main-content">
                <header className="app-header"> 
                    <div className="header-content">
                        <h1>Agri-Advisor AI</h1>
                        <p>{currentTranslation.subtitle}</p>
                    </div>
                </header>
                <div className="input-area-wrapper">
                    <InputArea 
                        {...{input, setInput, isRecording, isTranscribing, handleAudioClick}}
                        onSendMessage={handleSendMessage} 
                        toggleKeyboard={() => setShowKeyboard(!showKeyboard)}
                        placeholderText={currentTranslation.placeholder}
                        tooltipAudio={currentTranslation.tooltipAudio}
                        tooltipKeyboard={currentTranslation.tooltipKeyboard}
                        tooltipSend={currentTranslation.tooltipSend}
                    />
                </div>
            </main>
            {showKeyboard && 
                <OnScreenKeyboard 
                    onKeyPress={handleKeyPress} 
                    currentLanguage={globalLanguage}
                    onLanguageChange={handleLanguageChange}
                />
            }
        </div>
    );

    const renderActiveChat = () => (
        <div className="app-container chat-active">
            <header className="app-header"> 
                <div className="header-content"><h1>Agri-Advisor AI</h1></div>
            </header>
            <ChatInterface messages={messages} />
            <div className="chat-input-section">
                {showKeyboard && 
                    <OnScreenKeyboard 
                        onKeyPress={handleKeyPress}
                        currentLanguage={globalLanguage}
                        onLanguageChange={handleLanguageChange}
                    />
                }
                <div className="input-area-wrapper">
                    <InputArea 
                        {...{input, setInput, isRecording, isTranscribing, handleAudioClick}}
                        onSendMessage={handleSendMessage} 
                        toggleKeyboard={() => setShowKeyboard(!showKeyboard)}
                        placeholderText={currentTranslation.placeholder}
                        tooltipAudio={currentTranslation.tooltipAudio}
                        tooltipKeyboard={currentTranslation.tooltipKeyboard}
                        tooltipSend={currentTranslation.tooltipSend}
                    />
                </div>
            </div>
        </div>
    );

    return (
        <div className={`app-layout ${isSidebarOpen ? 'sidebar-open' : ''}`}>
            {/* The open button is now only for when a user explicitly closes the sidebar */}
            {!isSidebarOpen && (
                <button className="sidebar-open-button" onClick={toggleSidebar}>
                    <FiMenu />
                </button>
            )}

            <Sidebar
                isOpen={isSidebarOpen}
                chatHistory={chatHistory} 
                onClose={toggleSidebar}
                onProfileClick={toggleProfileMenu}
                isProfileMenuOpen={isProfileMenuOpen}
                onNewChat={handleNewChat} 
                isChatActive={isChatActive}
                onLogout={onLogout}
                onLoadChat={loadChat}
                onDeleteChat={handleDeleteChat}
                translations={currentTranslation} 
                onLanguageChange={handleLanguageChange}
                globalLanguage={globalLanguage}
                ref={profileMenuRef}
            />

            <div className="main-content-area">
                {isChatActive ? renderActiveChat() : renderLandingPage()}
            </div>
        </div>
    );
}

export default AgriAdvisorApp;
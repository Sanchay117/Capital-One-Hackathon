import React, { useState, useRef, useEffect } from 'react';
import '../App.css'; 
import ChatInterface from './ChatInterface';
import InputArea from './InputArea';
import OnScreenKeyboard from './OnScreenKeyboard';
import LanguageSelector from './LanguageSelector';
import Sidebar from './Sidebar'; // The sidebar component
import { translations } from '../translations';
import { FiMenu } from 'react-icons/fi'; // Icon for the open button

function AgriAdvisorApp() {
    // State for sidebar and profile menu
    const [isSidebarOpen, setIsSidebarOpen] = useState(false); // Sidebar now starts closed by default
    const [isProfileMenuOpen, setIsProfileMenuOpen] = useState(false);
    const profileMenuRef = useRef(null);

    // Dummy data for chat history
    const dummyChatHistory = [
        { id: 1, title: 'Fertilizer recommendations for wheat' },
        { id: 2, title: 'Best time to plant corn in my area' },
        { id: 3, title: 'How to handle pest infestation' },
        { id: 4, title: 'Crop rotation strategies' },
        { id: 5, title: 'Soil health and nutrient management' },
        { id: 6, title: 'Irrigation techniques for dry seasons' },
        { id: 7, title: 'Market prices for soybeans' },
    ];

    // Original state for the chat application
    const [messages, setMessages] = useState([]);
    const [showKeyboard, setShowKeyboard] = useState(false);
    const [input, setInput] = useState('');
    const [isChatActive, setIsChatActive] = useState(false);
    const [globalLanguage, setGlobalLanguage] = useState('en');
    const [isRecording, setIsRecording] = useState(false);
    const mediaRecorder = useRef(null);
    const audioChunks = useRef([]);

    // Handlers for sidebar and profile
    const toggleSidebar = () => setIsSidebarOpen(!isSidebarOpen);
    const toggleProfileMenu = () => setIsProfileMenuOpen(!isProfileMenuOpen);
    const handleLogout = () => {
        console.log("Logout clicked!");
        alert("Logout functionality would be handled here.");
    };

    // Effect to close profile menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (profileMenuRef.current && !profileMenuRef.current.contains(event.target)) {
                setIsProfileMenuOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [profileMenuRef]);

    // Original functions for the chat application (unchanged)
    const startRecording = () => { /* ...your existing code... */ };
    const stopRecording = () => { /* ...your existing code... */ };
    const handleAudioClick = () => { /* ...your existing code... */ };
    const handleSendMessage = (text) => { /* ...your existing code... */ };
    const handleKeyPress = (key) => { /* ...your existing code... */ };

    const containerClassName = `app-container ${isChatActive ? 'chat-active' : 'chat-inactive'}`;
    const currentTranslation = translations[globalLanguage];

    return (
        <div className={`app-layout ${isSidebarOpen ? 'sidebar-open' : ''}`}>
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
                {!isSidebarOpen && (
                    <button className="sidebar-open-button" onClick={toggleSidebar}>
                        <FiMenu />
                    </button>
                )}

                <div className={containerClassName}>
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
                                tooltipAudio={currentTranslation.tooltipAudio}
                                tooltipKeyboard={currentTranslation.tooltipKeyboard}
                                tooltipSend={currentTranslation.tooltipSend}
                                isRecording={isRecording}
                                handleAudioClick={handleAudioClick}
                            />
                        </div>
                    </main>
                    {showKeyboard && <OnScreenKeyboard onKeyPress={handleKeyPress} />}
                    {isChatActive && <ChatInterface messages={messages} />}
                </div>
            </div>
        </div>
    );
}

export default AgriAdvisorApp;
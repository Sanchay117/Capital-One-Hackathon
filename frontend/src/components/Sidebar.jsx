import React, { useState } from 'react';
// Import all necessary icons
import { FiMessageSquare, FiX, FiUser, FiLogOut, FiPlus, FiTrash2, FiChevronRight } from 'react-icons/fi';
// THE FIX: Import the new, dedicated modal for changing the language
import LanguageChangeModal from './LanguageChangeModal'; 

const Sidebar = React.forwardRef(({
    isOpen,
    chatHistory,
    onClose,
    onProfileClick,
    isProfileMenuOpen,
    onLogout,
    onNewChat,
    isChatActive,
    onLoadChat,
    onDeleteChat,
    onLanguageChange,
    globalLanguage,
    translations = {}, 
}, ref) => {
    
    const [isLanguageModalOpen, setIsLanguageModalOpen] = useState(false);

    const handleDeleteClick = (e, chatId) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to delete this chat? This action cannot be undone.")) {
            onDeleteChat(chatId);
        }
    };

    return (
        <>
            <div className={`sidebar ${isOpen ? 'open' : 'closed'}`} ref={ref}>
                <div className="sidebar-header">
                    <h3>{translations.sidebarHeader || 'History'}</h3>
                    <button className="sidebar-close-button" onClick={onClose}>
                        <FiX />
                    </button>
                </div>

                <div className="new-chat-container">
                    <button 
                        className="new-chat-button" 
                        onClick={onNewChat}
                        disabled={!isChatActive} 
                    >
                        <FiPlus />
                        <span>{translations.newChatButton || 'New Chat'}</span>
                    </button>
                </div>

                <div className="chat-history-list">
                    {(chatHistory || []).map((chat) => (
                        <div 
                            key={chat.id} 
                            className="chat-history-item"
                            onClick={() => onLoadChat(chat.id)}
                        >
                            <div className="chat-item-title">
                                <FiMessageSquare className="chat-icon" />
                                <span>{chat.title}</span>
                            </div>
                            <button 
                                className="delete-chat-button"
                                onClick={(e) => handleDeleteClick(e, chat.id)}
                                title="Delete chat"
                            >
                                <FiTrash2 />
                            </button>
                        </div>
                    ))}
                </div>

                <div className="profile-footer">
                    {isProfileMenuOpen && (
                        <div className="profile-menu">
                            {/* This is now a button that OPENS the language modal */}
                            <button onClick={() => setIsLanguageModalOpen(true)} className="profile-menu-item">
                                <span>{translations.changeLanguage || 'Change Language'}</span>
                                <FiChevronRight />
                            </button>
                            
                            <div className="profile-menu-divider"></div>

                            <button onClick={onLogout} className="profile-menu-item">
                                <FiLogOut />
                                <span>{translations.logout || 'Logout'}</span>
                            </button>
                        </div>
                    )}
                    <button className="profile-button" onClick={onProfileClick}>
                        <div className="profile-avatar">
                            <FiUser />
                        </div>
                        <span className="profile-name">{translations.userProfile || 'User Profile'}</span>
                    </button>
                </div>
            </div>

            {/* Render the language modal conditionally based on its state */}
            {isLanguageModalOpen && (
                <LanguageChangeModal
                    currentLanguage={globalLanguage}
                    onLanguageChange={onLanguageChange}
                    onClose={() => setIsLanguageModalOpen(false)}
                    translations={translations}
                />
            )}
        </>
    );
});

export default Sidebar;
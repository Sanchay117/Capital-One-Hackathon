import React from 'react';
import { FiMessageSquare, FiX, FiUser, FiLogOut, FiPlus } from 'react-icons/fi';

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
    translations = {}, // Provide a default empty object to prevent crashes
}, ref) => {
    return (
        <div className={`sidebar ${isOpen ? 'open' : 'closed'}`} ref={ref}>
            <div className="sidebar-header">
                {/* Use translated text with a fallback */}
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
                        <FiMessageSquare className="chat-icon" />
                        <span>{chat.title}</span>
                    </div>
                ))}
            </div>

            <div className="profile-footer">
                {isProfileMenuOpen && (
                    <div className="profile-menu">
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
    );
});

export default Sidebar;
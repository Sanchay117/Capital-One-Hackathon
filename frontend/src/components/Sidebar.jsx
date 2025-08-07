import React from 'react';
import { FiMessageSquare, FiX, FiUser, FiLogOut } from 'react-icons/fi';

const Sidebar = ({
    isOpen,
    chatHistory,
    onClose,
    onProfileClick,
    isProfileMenuOpen,
    onLogout,
}) => {
    return (
        <div className={`sidebar ${isOpen ? 'open' : ''}`}>
            <div className="sidebar-header">
                <h3>Chat History</h3>
                <button className="sidebar-close-button" onClick={onClose}>
                    <FiX />
                </button>
            </div>

            <div className="chat-history-list">
                {/* THE FIX: This code ensures every item gets an icon, creating a consistent UI. */}
                {chatHistory.map((chat, index) => (
                    <div key={index} className="chat-history-item">
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
                            <span>Logout</span>
                        </button>
                    </div>
                )}
                <button className="profile-button" onClick={onProfileClick}>
                    <div className="profile-avatar">
                        <FiUser />
                    </div>
                    <span className="profile-name">User Profile</span>
                </button>
            </div>
        </div>
    );
};

export default Sidebar;
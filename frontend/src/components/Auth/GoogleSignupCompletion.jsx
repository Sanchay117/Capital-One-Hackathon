import React, { useState } from 'react';
import LanguageSelection from './LanguageSelection';
import './Auth.css';

// This component assumes it will receive the user's name from the backend/router
const GoogleSignupCompletion = ({ userName = "User" }) => {
    const [preferredLanguage, setPreferredLanguage] = useState('en');

    const handleCompletionSubmit = (event) => {
        event.preventDefault();
        // In a real app, you would send the user's Google ID (which your backend
        // would have stored in a session) and the preferredLanguage to the backend.
        console.log(`Completing Google signup for ${userName} with language: ${preferredLanguage}`);
    };

    return (
        <div className="auth-page-container">
            <div className="auth-form-container">
                {/* Personalize the welcome message */}
                <h1 className="auth-title">Welcome, {userName}!</h1>
                <p className="auth-subtitle">Just one last step to personalize your experience.</p>
                
                <form className="auth-form" onSubmit={handleCompletionSubmit}>
                    <LanguageSelection
                        selectedLanguage={preferredLanguage}
                        setSelectedLanguage={setPreferredLanguage}
                    />

                    <button type="submit" className="auth-button">
                        Complete Signup
                    </button>
                </form>
            </div>
        </div>
    );
};

export default GoogleSignupCompletion;
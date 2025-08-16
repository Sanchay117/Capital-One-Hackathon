import React, { useState } from 'react';
import LanguageSelection from './LanguageSelection';
import './Auth.css';

const GoogleSignupCompletion = ({ userData, onLoginSuccess }) => {
    const [preferredLanguage, setPreferredLanguage] = useState('en');
    const [error, setError] = useState('');

    const handleCompletionSubmit = async (event) => {
        event.preventDefault();
        setError('');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/complete-google-signup/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    google_temp_token: userData.temp_token, // Send the temp token from the backend
                    preferred_language: preferredLanguage,
                }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to complete signup.');
            }
            onLoginSuccess(data); // The backend returns the final auth tokens
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="auth-page-container">
            <div className="auth-form-container">
                <h1 className="auth-title">Welcome, {userData.name}!</h1>
                <p className="auth-subtitle">Just one last step to personalize your experience.</p>
                {error && <p className="auth-error">{error}</p>}
                
                <form className="auth-form" onSubmit={handleCompletionSubmit}>
                    <LanguageSelection selectedLanguage={preferredLanguage} setSelectedLanguage={setPreferredLanguage} />
                    <button type="submit" className="auth-button">Complete Signup</button>
                </form>
            </div>
        </div>
    );
};

export default GoogleSignupCompletion;
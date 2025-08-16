import React, { useState, useEffect } from 'react';
import AgriAdvisorApp from './components/AgriAdvisorApp';
import LoginPage from './components/Auth/LoginPage';
import SignupPage from './components/Auth/SignupPage';
import GoogleSignupCompletion from './components/Auth/GoogleSignupCompletion';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [currentView, setCurrentView] = useState('login');
    const [googleUserData, setGoogleUserData] = useState(null);

    // This function runs when the app first loads
    useEffect(() => {
        // Check if there's a token in local storage to auto-login the user
        const token = localStorage.getItem('accessToken');
        if (token) {
            setIsAuthenticated(true);
        }
    }, []);

    const handleLoginSuccess = (data) => {
        // Store tokens and user info in local storage
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));
        setIsAuthenticated(true);
    };

    const handleGoogleSignupNeeded = (userData) => {
        // User is new, show them the language selection page
        setGoogleUserData(userData);
        setCurrentView('google-complete');
    };

    const handleLogout = () => {
        // Clear all session data and return to the login screen
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setCurrentView('login');
    };

    const toggleView = () => {
        setCurrentView(currentView === 'login' ? 'signup' : 'login');
    };

    if (isAuthenticated) {
        // THE FIX: Pass the handleLogout function as a prop
        return <AgriAdvisorApp onLogout={handleLogout} />;
    } else {
        switch (currentView) {
            case 'signup':
                return <SignupPage onToggleView={toggleView} onLoginSuccess={handleLoginSuccess} />;
            case 'google-complete':
                return <GoogleSignupCompletion userData={googleUserData} onLoginSuccess={handleLoginSuccess} />;
            default:
                return <LoginPage 
                    onToggleView={toggleView} 
                    onLoginSuccess={handleLoginSuccess} 
                    onGoogleSignupNeeded={handleGoogleSignupNeeded}
                />;
        }
    }
}

export default App;
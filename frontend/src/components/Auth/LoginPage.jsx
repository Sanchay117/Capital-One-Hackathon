import React, { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import './Auth.css';

const LoginPage = ({ onToggleView, onLoginSuccess, onGoogleSignupNeeded }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');

    // --- Standard Username/Password Login ---
    const handleFormSubmit = async (event) => {
        event.preventDefault();
        setError('');
        try {
            const response = await fetch('http://127.0.0.1:8000/api/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Login failed.');
            }
            onLoginSuccess(data);
        } catch (err) {
            setError(err.message);
        }
    };

    // --- Google Login ---
    const handleGoogleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setError('');
            try {
                const response = await fetch('http://127.0.0.1:8000/api/login/google/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: tokenResponse.access_token }),
                });
                const data = await response.json();
                if (!response.ok) {
                    throw new Error(data.error || 'Google login failed.');
                }
                
                if (data.is_new_user) {
                    onGoogleSignupNeeded(data.user_data);
                } else {
                    onLoginSuccess(data);
                }
            } catch (err) {
                setError(err.message);
            }
        },
        onError: () => {
            setError('Google login failed. Please try again.');
        },
    });

    return (
        <div className="auth-page-container">
            <div className="auth-form-container">
                <h1 className="auth-title">Welcome Back</h1>
                <p className="auth-subtitle">Login to access your farm's dashboard.</p>
                {error && <p className="auth-error">{error}</p>}

                <button className="google-button" onClick={() => handleGoogleLogin()}>
                    {/* (SVG for Google logo remains the same) */}
                    Continue with Google
                </button>

                <div className="divider">...</div>

                <form className="auth-form" onSubmit={handleFormSubmit}>
                    <div className="input-group">
                        <label htmlFor="email">Email</label>
                        <input type="email" id="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password">Password</label>
                        <div className="password-input-wrapper">
                            <input type={showPassword ? 'text' : 'password'} id="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                            <span className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                                {showPassword ? <FiEyeOff /> : <FiEye />}
                            </span>
                        </div>
                    </div>
                    <button type="submit" className="auth-button">Login</button>
                </form>

                <p className="toggle-link-container">
                    New User? <span className="toggle-link" onClick={onToggleView}>Click to Signup</span>
                </p>
            </div>
        </div>
    );
};

export default LoginPage;
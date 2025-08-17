import React, { useState } from 'react';
import { FiEye, FiEyeOff } from 'react-icons/fi';
import LanguageSelection from './LanguageSelection';
import { ReactComponent as GoogleLogo } from '../../Assets/google.svg';
import './Auth.css';

const SignupPage = ({ onToggleView, onLoginSuccess }) => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [preferredLanguage, setPreferredLanguage] = useState('en');
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const handleSignupSubmit = async (event) => {
        event.preventDefault();
        if (password !== confirmPassword) {
            setError("Passwords do not match.");
            return;
        }
        setError('');
        try {
            const regResponse = await fetch('http://127.0.0.1:8000/api/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, email, password, preferred_language: preferredLanguage }),
            });
            if (!regResponse.ok) {
                const errData = await regResponse.json();
                throw new Error(JSON.stringify(errData));
            }

            const loginResponse = await fetch('http://127.0.0.1:8000/api/login/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            const loginData = await loginResponse.json();
            if (!loginResponse.ok) throw new Error(loginData.detail);
            onLoginSuccess(loginData);

        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div className="auth-page-container">
            <div className="auth-form-container">
                <h1 className="auth-title">Create Your Account</h1>
                {error && <p className="auth-error">{error}</p>}
                
                <button className="google-button">
                    <GoogleLogo className="google-logo-svg" />
                    Sign Up with Google
                </button>

                <div className="divider">
                    <span className="divider-line"></span>
                    <span className="divider-text">OR</span>
                    <span className="divider-line"></span>
                </div>

                <form className="auth-form" onSubmit={handleSignupSubmit}>
                    <div className="input-group">
                        <label htmlFor="username-signup">Username</label>
                        <input type="text" id="username-signup" value={username} onChange={(e) => setUsername(e.target.value)} required />
                    </div>
                    <div className="input-group">
                        <label htmlFor="email-signup">Email</label>
                        <input type="email" id="email-signup" value={email} onChange={(e) => setEmail(e.target.value)} required />
                    </div>
                    <div className="input-group">
                        <label htmlFor="password-signup">Password</label>
                        <div className="password-input-wrapper">
                             <input type={showPassword ? 'text' : 'password'} id="password-signup" value={password} onChange={(e) => setPassword(e.target.value)} required />
                             <span className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>{showPassword ? <FiEyeOff /> : <FiEye />}</span>
                        </div>
                    </div>
                    <div className="input-group">
                        <label htmlFor="confirm-password-signup">Confirm Password</label>
                        <div className="password-input-wrapper">
                             <input type={showConfirmPassword ? 'text' : 'password'} id="confirm-password-signup" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
                             <span className="password-toggle-icon" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>{showConfirmPassword ? <FiEyeOff /> : <FiEye />}</span>
                        </div>
                    </div>
                    <LanguageSelection selectedLanguage={preferredLanguage} setSelectedLanguage={setPreferredLanguage} />
                    <button type="submit" className="auth-button">Create Account</button>
                </form>

                <p className="toggle-link-container">
                    Already have an account? <span className="toggle-link" onClick={onToggleView}>Click to Login</span>
                </p>
            </div>
        </div>
    );
};

export default SignupPage;

import React, { useState } from 'react';
// The FaGoogle import is now removed
import { FiEye, FiEyeOff } from 'react-icons/fi';
import './Auth.css';

const SignupPage = ({ onToggleView }) => {
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    return (
        <div className="auth-page-container">
            <div className="auth-form-container">
                <h1 className="auth-title">Create Your Account</h1>
                <p className="auth-subtitle">Get started with Agri-Advisor AI.</p>

                <button className="google-button">
                    {/* THE FIX: Replaced the icon component with an inline SVG */}
                    <svg
                        className="google-logo-svg"
                        viewBox="0 0 48 48"
                        width="24px"
                        height="24px"
                    >
                        <path
                            fill="#EA4335"
                            d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"
                        ></path>
                        <path
                            fill="#4285F4"
                            d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"
                        ></path>
                        <path
                            fill="#FBBC05"
                            d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"
                        ></path>
                        <path
                            fill="#34A853"
                            d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.52 1.7-5.74 2.65-9.16 2.65-6.3 0-11.6-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"
                        ></path>
                        <path fill="none" d="M0 0h48v48H0z"></path>
                    </svg>
                    Sign Up with Google
                </button>

                <div className="divider">
                    <span className="divider-line"></span>
                    <span className="divider-text">OR</span>
                    <span className="divider-line"></span>
                </div>

                <form className="auth-form">
                    <div className="input-group">
                        <label htmlFor="username-signup">Username</label>
                        <input type="text" id="username-signup" placeholder="Choose a unique username" />
                    </div>

                    <div className="input-group">
                        <label htmlFor="password-signup">Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showPassword ? 'text' : 'password'}
                                id="password-signup"
                                placeholder="Create a strong password"
                            />
                            <span className="password-toggle-icon" onClick={() => setShowPassword(!showPassword)}>
                                {showPassword ? <FiEyeOff /> : <FiEye />}
                            </span>
                        </div>
                    </div>
                    
                    <div className="input-group">
                        <label htmlFor="confirm-password-signup">Confirm Password</label>
                        <div className="password-input-wrapper">
                            <input
                                type={showConfirmPassword ? 'text' : 'password'}
                                id="confirm-password-signup"
                                placeholder="Re-enter your password"
                            />
                            <span className="password-toggle-icon" onClick={() => setShowConfirmPassword(!showConfirmPassword)}>
                                {showConfirmPassword ? <FiEyeOff /> : <FiEye />}
                            </span>
                        </div>
                    </div>

                    <button type="submit" className="auth-button">
                        Create Account
                    </button>
                </form>

                <p className="toggle-link-container">
                    Already have an account? <span className="toggle-link" onClick={onToggleView}>Click to Login</span>
                </p>
            </div>
        </div>
    );
};

export default SignupPage;
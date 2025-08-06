import React, { useState, useEffect, useRef } from 'react';

// Language data for the dropdown
const languages = {
    en: "English",
    hi: "हिंदी (Hindi)",
    mr: "मराठी (Marathi)",
    ta: "தமிழ் (Tamil)",
    te: "తెలుగు (Telugu)",
    bn: "বাংলা (Bengali)",
    gu: "ગુજરાતી (Gujarati)",
    kn: "ಕನ್ನಡ (Kannada)",
    pa: "ਪੰਜਾਬੀ (Punjabi)"
};

const LanguageSelector = ({ setGlobalLanguage }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedLanguage, setSelectedLanguage] = useState('en');
    const wrapperRef = useRef(null);

    // Effect to close the dropdown if you click outside of it
    useEffect(() => {
        function handleClickOutside(event) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [wrapperRef]);

    const handleLanguageChange = (langKey) => {
        setSelectedLanguage(langKey);
        setGlobalLanguage(langKey);
        setIsOpen(false); // Close dropdown after selection
    };

    return (
        <div className="language-selector" ref={wrapperRef}>
            {/* The display button now uses flexbox for better alignment */}
            <button className="language-display" onClick={() => setIsOpen(!isOpen)}>
                <span className="language-name">{languages[selectedLanguage]}</span>
                <span className="language-arrow">▼</span>
            </button>

            {/* The dropdown menu, which appears only when 'isOpen' is true */}
            {isOpen && (
                <ul className="language-dropdown">
                    {Object.entries(languages).map(([key, name]) => (
                        <li
                            key={key}
                            className={`language-option ${selectedLanguage === key ? 'selected' : ''}`}
                            onClick={() => handleLanguageChange(key)}
                        >
                            {name}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default LanguageSelector;

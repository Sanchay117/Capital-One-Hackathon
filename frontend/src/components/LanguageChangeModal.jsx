import React, { useState } from 'react';

// This is a dedicated modal for changing language from the profile menu.
const LanguageChangeModal = ({ currentLanguage, onLanguageChange, onClose, translations = {} }) => {
    // This local state holds the user's selection *before* they click "Confirm".
    const [selectedLang, setSelectedLang] = useState(currentLanguage);

    const handleConfirm = () => {
        onLanguageChange(selectedLang); // Call the main function to update the language globally
        onClose(); // Close the modal
    };

    return (
        // The semi-transparent overlay that covers the screen
        <div className="language-modal-overlay" onClick={onClose}>
            {/* The modal content itself. We stop propagation so clicking inside doesn't close it. */}
            <div className="language-modal-content" onClick={(e) => e.stopPropagation()}>
                <h3>{translations.changeLanguage || 'Change Language'}</h3>
                
                <select 
                    className="language-modal-select" 
                    value={selectedLang} 
                    onChange={(e) => setSelectedLang(e.target.value)}
                >
                    <option value="en">English</option>
                    <option value="hi">हिंदी (Hindi)</option>
                    <option value="mr">मराठी (Marathi)</option>
                    <option value="ta">தமிழ் (Tamil)</option>
                    <option value="te">తెలుగు (Telugu)</option>
                    <option value="bn">বাংলা (Bengali)</option>
                    <option value="gu">ગુજરાતી (Gujarati)</option>
                    <option value="kn">ಕನ್ನಡ (Kannada)</option>
                    <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                    <option value="ur">اردو (Urdu)</option>
                    <option value="ml">മലയാളം (Malayalam)</option>
                    <option value="or">ଓଡ଼ିଆ (Odia)</option>
                </select>
                
                <button className="language-modal-confirm-btn" onClick={handleConfirm}>
                    {translations.confirm || 'Confirm'}
                </button>
            </div>
        </div>
    );
};

export default LanguageChangeModal;
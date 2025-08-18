import React, { useState } from 'react';

const LanguageChangeModal = ({ currentLanguage, onLanguageChange, onClose, translations = {} }) => {
    const [selectedLang, setSelectedLang] = useState(currentLanguage);

    const handleConfirm = () => {
        onLanguageChange(selectedLang);
        onClose();
    };

    return (
        <div className="language-modal-overlay" onClick={onClose}>
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

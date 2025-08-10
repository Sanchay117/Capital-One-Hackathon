import React from 'react';

// A reusable language selection dropdown
const LanguageSelection = ({ selectedLanguage, setSelectedLanguage }) => {
    return (
        <div className="input-group">
            <label htmlFor="language-select">Preferred Language</label>
            <select
                id="language-select"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
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
        </div>
    );
};

export default LanguageSelection;
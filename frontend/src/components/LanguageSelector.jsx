// src/components/LanguageSelector.js

import React from 'react';

const LanguageSelector = ({ setGlobalLanguage }) => {
  return (
    <div className="language-selector">
      <select onChange={(e) => setGlobalLanguage(e.target.value)}>
        <option value="en">English</option>
        <option value="hi">हिंदी (Hindi)</option>
        {/* Add more languages here */}
      </select>
    </div>
  );
};

export default LanguageSelector;
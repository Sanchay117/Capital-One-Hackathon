import React, { useState } from 'react';

// NEW, more complete keyboard layouts
const keyboards = {
  en: [
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', '\\'],
    ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'"],
    ['z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/'],
    [' ' , 'Backspace', 'Enter']
  ],
  hi: [
    ['~', '१', '२', '३', '४', '५', '६', '७', '८', '९', '०', '-', 'ऋ'],
    ['ौ', 'ै', 'ा', 'ी', 'ू', 'ब', 'ह', 'ग', 'द', 'ज', 'ड', 'ज्ञ', 'त्र'],
    ['ो', 'े', '्', 'ि', 'ु', 'प', 'र', 'क', 'त', 'च', 'ट', 'ष'],
    ['ं', 'म', 'न', 'व', 'ल', 'स', ',', '.', 'य', 'श'],
    [' ' , 'Backspace', 'Enter']
  ]
};

const OnScreenKeyboard = ({ onKeyPress }) => {
  const [language, setLanguage] = useState('en');

  // Helper to add special classes for styling
  const getKeyClassName = (key) => {
    if (key === 'Backspace' || key === 'Enter') return 'key key-wide key-functional';
    if (key === ' ') return 'key key-space';
    return 'key';
  };

  return (
    <div className="keyboard">
      <div className="language-switcher">
        <button onClick={() => setLanguage('en')} className={language === 'en' ? 'active' : ''}>English</button>
        <button onClick={() => setLanguage('hi')} className={language === 'hi' ? 'active' : ''}>हिंदी</button>
      </div>
      <div className="keyboard-layout">
        {keyboards[language].map((row, i) => (
          <div key={i} className="keyboard-row">
            {row.map(key => (
              <button key={key} onClick={() => onKeyPress(key)} className={getKeyClassName(key)}>
                {key}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default OnScreenKeyboard;
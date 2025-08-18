import React, { useState } from 'react';

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
  ],
  mr: [
    ['~', '१', '२', '३', '४', '५', '६', '७', '८', '९', '०', '-', 'ऋ'],
    ['ौ', 'ै', 'ा', 'ी', 'ू', 'ब', 'ह', 'ग', 'द', 'ज', 'ड', 'ज्ञ', 'त्र'],
    ['ो', 'े', '्', 'ि', 'ु', 'प', 'र', 'क', 'त', 'च', 'ट', 'ष'],
    ['ं', 'म', 'न', 'व', 'ल', 'स', ',', '.', 'य', 'श'],
    [' ' , 'Backspace', 'Enter']
  ],
  ta: [
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['க்', 'வ்', 'ச்', 'ஞ்', 'ட்', 'ண்', 'த்', 'ந்', 'ப்', 'ம்', 'ய்', 'ர்', 'ல்'],
    ['ா', 'ி', 'ீ', 'ு', 'ூ', 'ெ', 'ே', 'ை', 'ொ', 'ோ', 'ௌ'],
    ['ழ்', 'ள்', 'ற்', 'ன்', 'ஶ', 'ஷ', 'ஸ', 'ஹ', 'க்ஷ', 'ஸ்ரீ'],
    [' ' , 'Backspace', 'Enter']
  ],
  te: [
    ['~', '౧', '౨', '౩', '౪', '౫', '౬', '౭', '౮', '౯', '౦', '-', 'ఋ'],
    ['ౌ', 'ై', 'ా', 'ీ', 'ూ', 'బ', 'హ', 'గ', 'ద', 'జ', 'డ', 'ఙ', 'ఞ'],
    ['ో', 'ే', '్', 'ి', 'ు', 'ప', 'ర', 'క', 'త', 'చ', 'ట', 'ష'],
    ['ం', 'మ', 'న', 'వ', 'ల', 'స', ',', '.', 'య', 'శ'],
    [' ' , 'Backspace', 'Enter']
  ],
  bn: [
    ['~', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯', '০', '-', 'ঋ'],
    ['ৌ', 'ৈ', 'া', 'ী', 'ূ', 'ব', 'হ', 'গ', 'দ', 'জ', 'ড', 'ঞ', 'ত্র'],
    ['ো', 'ে', '্', 'ি', 'ু', 'প', 'র', 'ক', 'ত', 'চ', 'ট', 'ষ'],
    ['ং', 'ম', 'ন', 'ব', 'ল', 'স', ',', '.', 'য়', 'শ'],
    [' ' , 'Backspace', 'Enter']
  ],
  gu: [
    ['~', '૧', '૨', '૩', '૪', '૫', '૬', '૭', '૮', '૯', '૦', '-', 'ઋ'],
    ['ૌ', 'ૈ', 'ા', 'ી', 'ૂ', 'બ', 'હ', 'ગ', 'દ', 'જ', 'ડ', 'ઞ', 'ત્ર'],
    ['ો', 'ે', '્', 'િ', 'ુ', 'પ', 'ર', 'ક', 'ત', 'ચ', 'ટ', 'ષ'],
    ['ં', 'મ', 'ન', 'વ', 'લ', 'સ', ',', '.', 'ય', 'શ'],
    [' ' , 'Backspace', 'Enter']
  ],
  kn: [
    ['~', '೧', '೨', '೩', '೪', '೫', '೬', '೭', '೮', '೯', '೦', '-', 'ಋ'],
    ['ೌ', 'ೈ', 'ಾ', 'ೀ', 'ೂ', 'ಬ', 'ಹ', 'ಗ', 'ದ', 'ಜ', 'ಡ', 'ಞ', 'ತ್ರ'],
    ['ೋ', 'ೇ', '್', 'ಿ', 'ು', 'ಪ', 'ರ', 'ಕ', 'ತ', 'ಚ', 'ಟ', 'ಷ'],
    ['ಂ', 'ಮ', 'ನ', 'ವ', 'ಲ', 'ಸ', ',', '.', 'ಯ', 'ಶ'],
    [' ' , 'Backspace', 'Enter']
  ],
  pa: [
    ['~', '੧', '੨', '੩', '੪', '੫', '੬', '੭', '੮', '੯', '੦', '-', 'ਖ਼'],
    ['ਔ', 'ਐ', 'ਆ', 'ਈ', 'ਊ', 'ਬ', 'ਹ', 'ਗ', 'ਦ', 'ਜ', 'ਡ', 'ਙ', 'ਤ੍ਰ'],
    ['ਓ', 'ਏ', '੍', 'ਿ', 'ੁ', 'ਪ', 'ਰ', 'ਕ', 'ਤ', 'ਚ', 'ਟ', 'ਸ਼'],
    ['ਂ', 'ਮ', 'ਨ', 'ਵ', 'ਲ', 'ਸ', ',', '.', 'ਯ', 'ਖ'],
    [' ' , 'Backspace', 'Enter']
  ],
  ur: [
    ['`', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '='],
    ['ق', 'و', 'ر', 'ت', 'ے', 'ء', 'ی', 'ہ', 'پ', ']', '[', '\\'],
    ['ا', 'س', 'د', 'ف', 'گ', 'ح', 'ج', 'ک', 'ل', ';', 'ط'],
    ['ژ', 'ش', 'چ', 'ڤ', 'ب', 'ن', 'م', '،', '۔', 'ض'],
    [' ' , 'Backspace', 'Enter']
  ],
  ml: [
    ['~', '൧', '൨', '൩', '൪', '൫', '൬', '൭', '൮', '൯', '൦', '-', 'ഋ'],
    ['ൌ', 'ൈ', 'ാ', 'ീ', 'ൂ', 'ബ', 'ഹ', 'ഗ', 'ദ', 'ജ', 'ഡ', 'ഞ', 'ത്ര'],
    ['ോ', 'േ', '്', 'ി', 'ു', 'പ', 'ര', 'ക', 'ത', 'ച', 'ട', 'ഷ'],
    ['ം', 'മ', 'ന', 'വ', 'ല', 'സ', ',', '.', 'യ', 'ശ'],
    [' ' , 'Backspace', 'Enter']
  ],
  or: [
    ['~', '୧', '୨', '୩', '୪', '୫', '୬', '୭', '୮', '୯', '୦', '-', 'ଋ'],
    ['ୌ', 'ୈ', 'ା', 'ୀ', 'ୂ', 'ବ', 'ହ', 'ଗ', 'ଦ', 'ଜ', 'ଡ', 'ଞ', 'ତ୍ର'],
    ['ୋ', 'େ', '୍', 'ି', 'ୁ', 'ପ', 'ର', 'କ', 'ତ', 'ଚ', 'ଟ', 'ଷ'],
    ['ଂ', 'ମ', 'ନ', 'ବ', 'ଲ', 'ସ', ',', '.', 'ୟ', 'ଶ'],
    [' ' , 'Backspace', 'Enter']
  ]
};

const OnScreenKeyboard = ({ onKeyPress, currentLanguage, onLanguageChange }) => {

  const getKeyClassName = (key) => {
    if (key === 'Backspace' || key === 'Enter') return 'key key-wide key-functional';
    if (key === ' ') return 'key key-space';
    return 'key';
  };

  return (
    <div className="keyboard">
      <div className="language-switcher">
        <button onClick={() => onLanguageChange('en')} className={currentLanguage === 'en' ? 'active' : ''}>English</button>
        <button onClick={() => onLanguageChange('hi')} className={currentLanguage === 'hi' ? 'active' : ''}>हिंदी</button>
        <button onClick={() => onLanguageChange('mr')} className={currentLanguage === 'mr' ? 'active' : ''}>मराठी</button>
        <button onClick={() => onLanguageChange('ta')} className={currentLanguage === 'ta' ? 'active' : ''}>தமிழ்</button>
        <button onClick={() => onLanguageChange('te')} className={currentLanguage === 'te' ? 'active' : ''}>తెలుగు</button>
        <button onClick={() => onLanguageChange('bn')} className={currentLanguage === 'bn' ? 'active' : ''}>বাংলা</button>
        <button onClick={() => onLanguageChange('gu')} className={currentLanguage === 'gu' ? 'active' : ''}>ગુજરાતી</button>
        <button onClick={() => onLanguageChange('kn')} className={currentLanguage === 'kn' ? 'active' : ''}>ಕನ್ನಡ</button>
        <button onClick={() => onLanguageChange('pa')} className={currentLanguage === 'pa' ? 'active' : ''}>ਪੰਜਾਬੀ</button>
        <button onClick={() => onLanguageChange('ur')} className={currentLanguage === 'ur' ? 'active' : ''}>اردو</button>
        <button onClick={() => onLanguageChange('ml')} className={currentLanguage === 'ml' ? 'active' : ''}>മലയാളം</button>
        <button onClick={() => onLanguageChange('or')} className={currentLanguage === 'or' ? 'active' : ''}>ଓଡ଼ିଆ</button>
      </div>
      <div className="keyboard-layout">
        {(keyboards[currentLanguage] || keyboards.en).map((row, i) => (
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

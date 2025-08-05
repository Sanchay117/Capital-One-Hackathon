// src/components/InputArea.js

import React from 'react';
import sendIcon from '../Assets/send-icon.svg';
import microphoneIcon from '../Assets/microphone-icon.svg';
import keyboardIcon from '../Assets/keyboard-icon.svg';
import stopIcon from '../Assets/stop-icon.svg'; // Import the new stop icon

const InputArea = ({ 
  input, 
  setInput, 
  onSendMessage, 
  toggleKeyboard,
  placeholderText,
  tooltipAudio,
  tooltipKeyboard,
  tooltipSend,
  // New props for audio recording
  isRecording,
  handleAudioClick
}) => {
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      onSendMessage();
    }
  };

  return (
    <div className="input-area">
      {/* The audio button now has conditional logic and styling */}
      <button 
        className={`icon-button ${isRecording ? 'recording-pulse' : ''}`} 
        title={isRecording ? "Stop Recording" : tooltipAudio} 
        onClick={handleAudioClick}
      >
        <img src={isRecording ? stopIcon : microphoneIcon} alt="Audio Input" />
      </button>

      <input
        type="text"
        value={input}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        placeholder={isRecording ? "Recording..." : placeholderText}
        disabled={isRecording} // Disable typing while recording
      />
      
      <button className="icon-button" title={tooltipKeyboard} onClick={toggleKeyboard}>
        <img src={keyboardIcon} alt={tooltipKeyboard} />
      </button>
      
      <button className="send-button" title={tooltipSend} onClick={onSendMessage}>
        <img src={sendIcon} alt={tooltipSend} />
      </button>
    </div>
  );
};

export default InputArea;
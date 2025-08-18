import React from 'react';
import sendIcon from '../Assets/send-icon.svg';
import microphoneIcon from '../Assets/microphone-icon.svg';
import keyboardIcon from '../Assets/keyboard-icon.svg';
import stopIcon from '../Assets/stop-icon.svg';

const InputArea = ({ 
  input, 
  setInput, 
  onSendMessage, 
  toggleKeyboard,
  placeholderText,
  tooltipAudio,
  tooltipKeyboard,
  tooltipSend,
  isRecording,
  isTranscribing,
  handleAudioClick
}) => {
  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      onSendMessage(input);
    }
  };

  const getPlaceholder = () => {
    if (isRecording) return "Recording... Click stop when done.";
    if (isTranscribing) return "Transcribing audio, please wait...";
    return placeholderText;
  };

  return (
    <div className="input-area">
      <button 
        className={`icon-button ${isRecording ? 'recording-pulse' : ''}`} 
        title={isRecording ? "Stop Recording" : tooltipAudio} 
        // Disable the mic button while transcribing to prevent conflicts
        disabled={isTranscribing} 
        onClick={handleAudioClick}
      >
        <img src={isRecording ? stopIcon : microphoneIcon} alt="Audio Input" />
      </button>

      <input
        type="text"
        value={input}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        placeholder={getPlaceholder()}
        disabled={isRecording || isTranscribing}
      />
      
      <button className="icon-button" title={tooltipKeyboard} onClick={toggleKeyboard}>
        <img src={keyboardIcon} alt={tooltipKeyboard} />
      </button>
      
      <button className="send-button" title={tooltipSend} onClick={() => onSendMessage(input)}>
        <img src={sendIcon} alt={tooltipSend} />
      </button>
    </div>
  );
};

export default InputArea;

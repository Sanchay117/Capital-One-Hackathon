import React, { useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatInterface = ({ messages }) => {
  const endOfMessagesRef = useRef(null);

  const scrollToBottom = () => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-interface">
      {messages.map((turn, index) => (
        <div key={index} className="chat-turn">
          {/* Section 1: The User's Prompt */}
          <div className="user-prompt-container">
            <div className="user-prompt">
              <p>{turn.prompt}</p>
            </div>
          </div>

          {/* Section 2: The AI's Response */}
          <div className="ai-response-container">
            <div className="ai-response">
              <ReactMarkdown>{turn.response}</ReactMarkdown>
            </div>
          </div>
        </div>
      ))}
      <div ref={endOfMessagesRef} />
    </div>
  );
};

export default ChatInterface;

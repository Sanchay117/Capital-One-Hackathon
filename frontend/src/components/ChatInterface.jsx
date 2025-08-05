// src/components/ChatInterface.js

import React, { useRef, useEffect } from 'react';

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
      {messages.map(message => (
        <div key={message.id} className={`message ${message.sender}`}>
          <p>{message.text}</p>
        </div>
      ))}
      <div ref={endOfMessagesRef} />
    </div>
  );
};

export default ChatInterface;
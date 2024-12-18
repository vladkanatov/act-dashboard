import React, { useState } from 'react';
import { sendMessage } from '../api';

function SendMessage({ token }) {
  const [igUsername, setIgUsername] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await sendMessage(token, igUsername, message);
    alert('Message sent!');
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Send Message</h2>
      <input
        type="text"
        placeholder="Instagram Username"
        value={igUsername}
        onChange={(e) => setIgUsername(e.target.value)}
      />
      <input
        type="text"
        placeholder="Message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
      />
      <button type="submit">Send</button>
    </form>
  );
}

export default SendMessage;

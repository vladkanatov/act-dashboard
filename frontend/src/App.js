import React, { useState } from 'react';
import Login from './components/Login';
import Register from './components/Register';
import Accounts from './components/Accounts';
import SendMessage from './components/SendMessage';
import AnalyzeFollowings from './components/AnalyzeFollowings';

function App() {
  const [token, setToken] = useState(null);

  return (
    <div className="App">
      <h1>Instagram Manager</h1>
      {!token ? (
        <>
          <Login setToken={setToken} />
          <Register />
        </>
      ) : (
        <>
          <Accounts token={token} />
          <SendMessage token={token} />
          <AnalyzeFollowings token={token} />
        </>
      )}
    </div>
  );
}

export default App;

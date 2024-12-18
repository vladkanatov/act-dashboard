import React, { useState } from 'react';
import { analyzeFollowings } from '../api';

function AnalyzeFollowings({ token }) {
  const [igUsername, setIgUsername] = useState('');
  const [analysis, setAnalysis] = useState(null);

  const handleAnalyze = async () => {
    const data = await analyzeFollowings(token, igUsername);
    setAnalysis(data);
  };

  return (
    <div>
      <h2>Analyze Followings</h2>
      <input
        type="text"
        placeholder="Instagram Username"
        value={igUsername}
        onChange={(e) => setIgUsername(e.target.value)}
      />
      <button onClick={handleAnalyze}>Analyze</button>
      {analysis && <pre>{JSON.stringify(analysis, null, 2)}</pre>}
    </div>
  );
}

export default AnalyzeFollowings;

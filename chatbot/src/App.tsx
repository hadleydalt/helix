import React, { useState } from 'react';
import './App.css';
import Chatbot from './Chatbot';
import Workspace from './Workspace';

const App: React.FC = () => {
  const [sequence, setSequence] = useState<string>('');

  const handleSequenceUpdate = (newSequence: string) => {
    setSequence(newSequence);
  };

  return (
    <div className="App">
      <Chatbot onSequenceUpdate={handleSequenceUpdate} />
      <Workspace sequence={sequence} />
    </div>
  );
};

export default App; 
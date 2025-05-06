import React from 'react';
import './Workspace.css';

interface WorkspaceProps {
  sequence?: string;
}

const Workspace: React.FC<WorkspaceProps> = ({ sequence }) => {
  const parseSequence = (sequence: string) => {
    // Messages will be separated by '---'
    const parts = sequence.split('---').map(part => part.trim()).filter(part => part.length > 0);
    return parts;
  };

  return (
    <div className="main-content">
      <div className="content-box">
        <h2>Generated Sequence</h2>
        {sequence ? (
          <div className="sequence-content">
            {parseSequence(sequence).map((message, index) => (
              <div key={index} className="message-box">
                <div className="message-header">
                  {index === 0 ? 'Initial Message' : `Follow-up ${index}`}
                </div>
                <div className="message-body">
                  {message.split('\n').map((line, lineIndex) => (
                    <p key={lineIndex}>{line}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p>No sequence generated yet. Start a conversation to generate a sequence.</p>
        )}
      </div>
    </div>
  );
};

export default Workspace; 
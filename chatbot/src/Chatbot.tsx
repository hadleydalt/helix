import React, { useState, useRef } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import axios from "axios";
import "./Chatbot.css";

interface Message {
  role: "user" | "assistant";
  content: string;
  type?: "gen" | "edit" | "delete" | "normal";
}

interface ChatbotProps {
  onSequenceUpdate: (sequence: string) => void;
}

const Chatbot: React.FC<ChatbotProps> = ({ onSequenceUpdate }) => {
  const [userInput, setUserInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const userId = "user123"; 
  const abortControllerRef = useRef<AbortController | null>(null);

  // note: this is not used in the current implementation.
  const resetChat = async (): Promise<void> => {
    setMessages([]); // Clear messages on frontend
    onSequenceUpdate(''); // Clear sequence
    try {
      await axios.post("http://127.0.0.1:5000/reset", { user_id: userId });
    } catch (error) {
      console.error("Error resetting chat:", error);
    }
  };

  const sendMessage = async (): Promise<void> => {
    if (!userInput || isStreaming) return;

    const newMessages: Message[] = [...messages, { role: "user", content: userInput, type: "normal" }];
    setMessages(newMessages);
    setUserInput("");
    setIsStreaming(true);

    // Add an empty assistant message that we'll update as we receive chunks
    setMessages(prev => [...prev, { role: "assistant", content: "", type: "normal" }]);

    try {
      // Create a new AbortController for this request
      abortControllerRef.current = new AbortController();

      const response = await fetch("http://127.0.0.1:5000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: userId,
          message: userInput
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let assistantMessage = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        
        if (chunk.includes('[GENERATING_SEQUENCE]')) {
          // Replace the current message with a sequence generation message
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              role: "assistant",
              content: "Generating sequence...",
              type: "gen"
            };
            return newMessages;
          });
        } else if (chunk.includes('[EDITING_SEQUENCE]')) {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              role: "assistant",
              content: "Editing sequence...",
              type: "edit"
            };
            return newMessages;
          });
        } else if (chunk.includes('[DELETING_STEP]')) {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[newMessages.length - 1] = {
              role: "assistant",
              content: "Deleting step from the sequence...",
              type: "delete"
            };
            return newMessages;
          });
          
        } else if (chunk.includes('[SEQUENCE_DATA]')) {
          // Extract and set the sequence data
          const sequenceData = chunk.replace('data: [SEQUENCE_DATA]', '').trim();
          onSequenceUpdate(sequenceData);
        } else if (chunk.startsWith('data: ')) {
          const content = chunk.slice(6).trim();
          // Only update the message if it's not a sequence data marker
          if (!content.includes('[SEQUENCE_DATA]')) {
            assistantMessage += content;
            setMessages(prev => {
              const newMessages = [...prev];
              newMessages[newMessages.length - 1] = {
                role: "assistant",
                content: assistantMessage,
                type: "normal"
              };
              return newMessages;
            });
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log('Request was aborted');
      } else {
        console.error("Error sending message:", error);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>): void => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div className="container">
      <div className="chat-container">
        {messages.map((msg, index) => (
          <div 
            key={index} 
            className={`message ${msg.role} ${msg.type === "gen" ? "gen-message" : msg.type === "edit" ? "edit-message" : msg.type === "delete" ? "delete-message" : ""}`}
          >
            <b>{msg.role === "user" ? "You" : "Helix"}</b>
            <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>
          </div>
        ))}
      </div>
      <div className="input-container">
        <input
          type="text"
          value={userInput}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setUserInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          className="message-input"
          disabled={isStreaming}
        />
        <button 
          onClick={sendMessage}
          className="send-button"
          disabled={isStreaming}
        >
          {isStreaming ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
};

export default Chatbot; 
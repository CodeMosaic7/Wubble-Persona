import { useState, useRef, useEffect } from 'react';
import { generateStory } from '../api/story';
import DownloadButton from './DownloadButton';
import '../styles/Chatbot.css';

const WELCOME = {
  id: 1,
  type: 'bot',
  content: '◈ Welcome to Persona. Share a moment — type it, photograph it, film it. I\'ll turn it into a cinematic audio story.',
  timestamp: new Date().toLocaleTimeString(),
};

export default function Chatbot({ isDark }) {
  const [messages, setMessages] = useState([WELCOME]);
  const [inputValue, setInputValue] = useState('');
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleFileChange = (e) => {
    const f = e.target.files[0];
    if (!f) return;
    setFile(f);
    if (f.type.startsWith('image')) {
      setFilePreview({ type: 'image', url: URL.createObjectURL(f), name: f.name });
    } else if (f.type.startsWith('video')) {
      setFilePreview({ type: 'video', url: URL.createObjectURL(f), name: f.name });
    } else if (f.type.startsWith('audio')) {
      setFilePreview({ type: 'audio', name: f.name });
    }
  };

  const clearFile = () => {
    setFile(null);
    setFilePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSend = async () => {
    if (!inputValue.trim() && !file) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue,
      filePreview,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    clearFile();
    setLoading(true);

    // Loading placeholder
    const loadingId = Date.now() + 1;
    setMessages((prev) => [...prev, {
      id: loadingId,
      type: 'bot',
      loading: true,
      content: '',
      timestamp: new Date().toLocaleTimeString(),
    }]);

    try {
  const data = await generateStory(
  userMessage.content || "Generate music for this",
  file
);

// data is now { audioUrl, duration, lyricsSections }
const botMessage = {
  id: loadingId,
  type: "bot",
  loading: false,
  content: data.audioUrl
    ? "✦ Your cinematic story is ready. Press play to hear your moment come alive."
    : "Something went wrong — no audio was returned.",
  audioUrl: data.audioUrl,
  lyricsSections: data.lyricsSections,
  timestamp: new Date().toLocaleTimeString(),
};

setMessages((prev) =>
  prev.map((m) => (m.id === loadingId ? botMessage : m))
);
} catch (err) {
  setMessages((prev) =>
    prev.map((m) =>
      m.id === loadingId
        ? {
            ...m,
            loading: false,
            content: `Error: ${err.response?.data?.detail || err.message}`,
            isError: true,
          }
        : m
    )
  );
} finally {
  setLoading(false);
}
  };

  return (
    <main className="chat-container">
      <div className="messages">
        {messages.map((msg) => (
          <div key={msg.id} className={`message ${msg.type} ${msg.isError ? 'error' : ''}`}>
            {msg.type === 'bot' && <div className="bot-avatar">◈</div>}

            <div className="message-bubble">
              {msg.loading ? (
                <div className="typing-indicator">
                  <span /><span /><span />
                  <em>Composing your story...</em>
                </div>
              ) : (
                <>
                  {/* User file preview */}
                  {msg.filePreview && (
                    <div className="file-preview-box">
                      {msg.filePreview.type === 'image' && (
                        <img src={msg.filePreview.url} alt="upload" />
                      )}
                      {msg.filePreview.type === 'video' && (
                        <video src={msg.filePreview.url} controls />
                      )}
                      {msg.filePreview.type === 'audio' && (
                        <div className="audio-name">🎵 {msg.filePreview.name}</div>
                      )}
                    </div>
                  )}

                  <p>{msg.content}</p>

                  {/* Audio player */}
                  {msg.audioUrl && (
                    <div className="audio-player">
                      <audio controls src={msg.audioUrl} />
                      <DownloadButton url={msg.audioUrl} />
                    </div>
                  )}
                </>
              )}
              <span className="timestamp">{msg.timestamp}</span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        {filePreview && (
          <div className="file-chip">
            <span>
              {filePreview.type === 'image' ? '🖼' : filePreview.type === 'video' ? '🎬' : '🎵'}
              {' '}{filePreview.name}
            </span>
            <button onClick={clearFile}>✕</button>
          </div>
        )}

        <div className="input-row">
          <button className="attach-btn" onClick={() => fileInputRef.current?.click()}>
            📎
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*,audio/*"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Describe your moment... 📸"
            className="message-input"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            className="send-button"
            disabled={loading || (!inputValue.trim() && !file)}
          >
            {loading ? '...' : '→'}
          </button>
        </div>
      </div>
    </main>
  );
}
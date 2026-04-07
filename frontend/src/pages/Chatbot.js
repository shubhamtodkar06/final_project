import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaPaperPlane, FaMicrophone, FaUpload, FaChevronLeft, FaVolumeUp } from 'react-icons/fa';
import './Chatbot.css';

const getAuthToken = () => localStorage.getItem('access');

const Chatbot = () => {
  const navigate = useNavigate();

  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! Please select a session or create a new one to start.' }
  ]);
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isBotTyping, setIsBotTyping] = useState(false);

  const socket = useRef(null);
  const audioPlayer = useRef(new Audio());
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Fetch sessions and connect websocket on mount
  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      navigate('/login');
      return;
    }

    // Fetch chat sessions
    const fetchSessions = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/chatbot/sessions/', {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setSessions(data);
          // Select the most recent session automatically
          if (data.length > 0) setCurrentSessionId(data[0].id);
        }
      } catch (e) {
        console.error("Failed to fetch sessions:", e);
      }
    };
    fetchSessions();

    // Setup websocket connection with token
    const wsUrl = `ws://localhost:8000/ws/chat/?token=${token}`;
    socket.current = new WebSocket(wsUrl);

    socket.current.onopen = () => console.log("WebSocket connected!");
    socket.current.onclose = () => console.log("WebSocket disconnected.");
    socket.current.onerror = (error) => console.error("WebSocket error:", error);

    socket.current.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'status' && data.value === 'typing') {
        setIsBotTyping(true);
        return;
      }

      if (data.type === 'partial') {
        setIsBotTyping(true);
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.sender === 'bot' && lastMsg.isPartial) {
            lastMsg.text = data.text;
            return [...prev];
          } else {
            return [...prev, { sender: 'bot', text: data.text, isPartial: true }];
          }
        });
      }

      if (data.type === 'final') {
        setIsBotTyping(false);
        
        // Check for audio data
        const audioSrc = data.audio_b64 ? `data:${data.content_type};base64,${data.audio_b64}` : null;

        // 1. Update the message text *first*.
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.isPartial) {
            lastMsg.text = data.reply;
            lastMsg.isPartial = false;
            lastMsg.audioSrc = audioSrc; // Add audio data to the message
            return [...prev];
          } else {
            return [...prev, { 
              sender: 'bot', 
              text: data.reply, 
              isPartial: false, 
              audioSrc: audioSrc 
            }];
          }
        });

        // 2. Now, try to play the audio
        if (audioSrc) {
          audioPlayer.current.src = audioSrc;
          const playPromise = audioPlayer.current.play();

          if (playPromise !== undefined) {
            playPromise.catch(error => {
              console.error("Audio playback failed:", error);
              // If it fails (NotAllowedError), update the last message to show a play button
              if (error.name === 'NotAllowedError') {
                setMessages(prev => {
                    const updatedMessages = [...prev];
                    const lastMsg = updatedMessages[updatedMessages.length - 1];
                    if (lastMsg && lastMsg.sender === 'bot') {
                      lastMsg.audioError = "Click to play audio";
                    }
                    return updatedMessages;
                });
              }
            });
          }
        }
      }

      if (data.error) {
        setIsBotTyping(false);
        setMessages(prev => [...prev, { sender: 'bot', text: `Error: ${data.error}` }]);
      }
    };

    return () => {
      if (socket.current) socket.current.close();
    };
  }, [navigate]);

  // Fetch messages for current session
  useEffect(() => {
    if (!currentSessionId) return;

    const fetchMessages = async () => {
      try {
        const token = getAuthToken();
        const res = await fetch(`http://localhost:8000/api/chatbot/sessions/${currentSessionId}/messages/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          // Map sender/content to sender/text
          const formatted = data.map(msg => ({ 
            sender: msg.sender, 
            text: msg.content 
          }));
          setMessages(formatted);
        }
      } catch (e) {
        console.error("Failed to fetch messages:", e);
      }
    };
    fetchMessages();
  }, [currentSessionId]);

  // Auto scroll on messages update
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const stopBotAudio = () => {
    if (audioPlayer.current && !audioPlayer.current.paused) {
      audioPlayer.current.pause();
      audioPlayer.current.currentTime = 0;
    }
  };

  // This is for TEXT input
  const handleSend = () => {
    if (!input.trim() || !currentSessionId || !socket.current || socket.current.readyState !== WebSocket.OPEN) return;
    stopBotAudio();

    setMessages(prev => [...prev, { sender: 'user', text: input }]);

    // This correctly sends tts: false for text
    socket.current.send(JSON.stringify({
      message: input,
      session_id: currentSessionId,
      tts: false,
    }));

    setInput('');
  };

  const handleFileClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (evt) => {
      // This implementation reads text-based files.
      const content = evt.target.result;
      const token = getAuthToken();
      try {
        const res = await fetch('http://localhost:8000/api/resources/add/', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ title: file.name, content }),
        });
        if (res.ok) {
          const data = await res.json();
          setMessages(prev => [...prev, {
            sender: 'bot',
            text: `Successfully added resource: ${file.name} (ID: ${data.id})`
          }]);
        } else {
          const err = await res.json();
          setMessages(prev => [...prev, {
            sender: 'bot',
            text: `Error uploading file: ${err.error || res.statusText}`
          }]);
        }
      } catch (err) {
        console.error("File upload failed:", err);
      }
    };
    // Use readAsText for .txt, .md, .csv etc. as per your API
    reader.readAsText(file);
    e.target.value = null;
  };

  const handleNewSession = async () => {
    try {
      const token = getAuthToken();
      const res = await fetch('http://localhost:8000/api/chatbot/sessions/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: 'New Chat Session' }),
      });
      if (res.ok) {
        const session = await res.json();
        setSessions(prev => [session, ...prev]);
        setCurrentSessionId(session.id);
        setMessages([]); // Clear messages for new session
      }
    } catch (e) {
      console.error("Failed to create session:", e);
    }
  };

  // --- THIS IS THE UPDATED FUNCTION ---
  // This function now implements voice input and sends tts: true
  const handleVoiceInput = () => {
    stopBotAudio(); // User interrupt! Stop bot audio.

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support Speech Recognition.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.interimResults = false;

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      
      // Automatically send the message
      if (transcript.trim() && currentSessionId && socket.current && socket.current.readyState === WebSocket.OPEN) {
        setMessages(prev => [...prev, { sender: 'user', text: transcript }]);
        
        // This sends tts: true to get audio back, fulfilling your request
        socket.current.send(JSON.stringify({
          message: transcript,
          session_id: currentSessionId,
          tts: true 
        }));
      }
      setInput(''); // Clear input just in case
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert("Microphone permission was denied. Please allow microphone access in your browser settings.");
      }
    };

    if (isListening) {
      recognition.stop();
    } else {
      recognition.start();
    }
  };
  
  return (
    <div className="chatbot-page">
      <aside className="chat-history-sidebar">
        <button className="neu-button back-button" onClick={() => navigate('/dashboard')}>
          <FaChevronLeft /> Dashboard
        </button>
        <button className="neu-button" onClick={handleNewSession} style={{ width: '100%', marginBottom: '10px' }}>
          + New Session
        </button>
        <h2>Chat Sessions</h2>
        <div className="history-list">
          {sessions.length === 0 && <p className="no-history">No sessions yet.</p>}
          {sessions.map((session) => (
            <div
              key={session.id}
              className={`history-item ${session.id === currentSessionId ? 'active' : ''}`}
              onClick={() => setCurrentSessionId(session.id)}
            >
              <p className="history-question">{session.title || 'Chat Session'}</p>
              <small>{new Date(session.created_at).toLocaleString()}</small>
            </div>
          ))}
        </div>
      </aside>

      <main className="chat-window">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.sender}`}>
              <div className="message-bubble">
                {msg.text}
                
                {/* --- THIS IS THE FIX --- */}
                {/* If audio failed, show this button */}
                {msg.audioError && (
                  <button className="neu-button play-audio-btn" onClick={() => {
                    audioPlayer.current.src = msg.audioSrc;
                    audioPlayer.current.play();
                    // Remove the error button once clicked
                    setMessages(prev => prev.map((m, index) => 
                      index === i ? { ...m, audioError: null } : m
                    ));
                  }}>
                    <FaVolumeUp /> {msg.audioError}
                  </button>
                )}
              </div>
            </div>
          ))}
          {isBotTyping && (
            <div className="message bot">
              <div className="message-bubble typing-indicator">
                <span/><span/><span/>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <div className="neu-input-bar">
            <button className="neu-icon" title="Upload Resource" onClick={handleFileClick}>
              <FaUpload />
            </button>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".txt,.md,.json,.csv" // Accepts text-based files as per API
              style={{ display: 'none' }}
            />
            <input
              type="text"
              placeholder="Type your message, or use the mic..."
              value={input}
              disabled={!currentSessionId}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && handleSend()}
            />
            {/* I have implemented the logic you requested:
              - Text input (handleSend) sends "tts: false"
              - Voice input (handleVoiceInput) sends "tts: true"
            */}
            <button
              className={`neu-icon mic-button ${isListening ? 'listening' : ''}`}
              title="Speak"
              disabled={!currentSessionId}
              onClick={handleVoiceInput}
            >
              <FaMicrophone />
            </button>
            <button
              className="neu-icon send-button"
              title="Send"
              disabled={!currentSessionId}
              onClick={handleSend}
            >
              <FaPaperPlane />
            </button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chatbot;
// src/pages/Chat.jsx
import { useEffect, useState } from "react";

function Chat() {
  const [socket, setSocket] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access");

    const ws = new WebSocket(`ws://localhost:8000/ws/chat/?token=${token}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "partial") {
        setMessages((prev) => [...prev, data.text]);
      }

      if (data.type === "final") {
        setMessages((prev) => [...prev, data.reply]);
      }
    };

    setSocket(ws);
  }, []);

  const sendMessage = () => {
    socket.send(
      JSON.stringify({
        message: input,
        filters: { subjects: ["Mathematics"], topics: ["Fractions"] },
        include_suggestions: true,
      })
    );
    setInput("");
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>AI Tutor</h2>

        <div style={{ maxHeight: "300px", overflow: "auto" }}>
          {messages.map((m, i) => (
            <p key={i}>{m}</p>
          ))}
        </div>

        <input value={input} onChange={(e) => setInput(e.target.value)} />
        <button className="neu-button" onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  );
}

export default Chat;
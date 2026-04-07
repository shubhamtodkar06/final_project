import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";

// Import your pages
import Index from "./pages/Index";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Chatbot from "./pages/Chatbot"; // <-- 1. IMPORT CHATBOT

// This imports your main style.css
import "./style.css"; 

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Index />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} /> 
        
        {/* 2. ADD THE ROUTE FOR THE CHATBOT */}
        <Route path="/chatbot" element={<Chatbot />} /> 
        
      </Routes>
    </Router>
  );
}

export default App;
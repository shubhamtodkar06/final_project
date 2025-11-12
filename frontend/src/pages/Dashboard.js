import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    FaUser, FaBell, FaSignOutAlt, FaQuoteLeft, 
    FaBook, FaUpload, FaEdit, FaChartPie, FaBrain,
    FaFileAlt // New icon for Notes
} from 'react-icons/fa';
import { MdOutlineAlarm } from 'react-icons/md';

// Import your new dashboard styles
import './Dashboard.css';

// Import the local image
import pieChartImage from './piechart.jpg'; 

const Dashboard = () => {
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState('8');

  const handleLogout = () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    navigate('/login');
  };

  const handleCourseChange = (e) => {
    setSelectedCourse(e.target.value);
  };

  const getSubjects = (course) => {
    switch(course) {
      case '5': return ['Mathematics', 'Science', 'English', 'Social Studies'];
      case '6': return ['Mathematics', 'Science', 'English', 'Social Studies', 'History'];
      case '7': return ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'History'];
      case '8': return ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'History', 'Geography'];
      case '9': return ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Economics'];
      case '10': return ['Mathematics', 'Physics', 'Chemistry', 'Biology', 'English', 'Computer Science'];
      default: return [];
    }
  };
  
  const subjects = getSubjects(selectedCourse);

  return (
    <div className="dashboard-container">
      
      {/* === 1. TOP HEADER (TITLE ON LEFT, ICONS ON RIGHT) === */}
      <header className="dashboard-header">
        <h1 className="dashboard-title">AI Tutor</h1>
        
        <div className="header-icon-group">
          {/* Icons have 'title' for hover tooltips */}
          <button className="header-icon neu-icon" title="Notifications">
            <FaBell />
          </button>
          <button className="header-icon neu-icon" title="Reminders">
            <MdOutlineAlarm />
          </button>
          
          <div className="profile-menu">
            <button 
              className="header-icon neu-icon profile-btn" 
              title="Profile"
              onClick={() => setProfileOpen(!profileOpen)}
            >
              <FaUser />
            </button>
            
            {profileOpen && (
              <div className="profile-dropdown login-card">
                <div className="user-info">
                  <FaUser />
                  <span>saniya10</span> {/* Get from user data */}
                </div>
                <button className="logout-button" onClick={handleLogout}>
                  <FaSignOutAlt /> Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* === 2. MAIN 2-COLUMN BODY === */}
      <div className="dashboard-body">

        {/* --- MAIN CONTENT (LEFT) --- */}
        <main className="dashboard-main-content">
          
          {/* --- THIS IS THE UPDATED CARD --- */}
          <div 
            className="dashboard-card card-chatbot" 
            onClick={() => navigate('/chatbot')} // This line is the update
          >
            <div className="neu-icon">
              <FaBrain /> {/* Updated Icon */}
            </div>
            <h2>AI Chatbot</h2>
            <p>Your personal AI assistant. Click here to start chatting!</p>
          </div>

          {/* Courses Card (Moved to main column) */}
          <div className="dashboard-card card-courses">
            <h2>My Courses</h2>
            <p>Select your grade to see your subjects:</p>
            <div className="form-group">
              <div className="neu-input">
                <FaBook className="input-icon" />
                <select value={selectedCourse} onChange={handleCourseChange}>
                  <option value="5">Grade 5</option>
                  <option value="6">Grade 6</option>
                  <option value="7">Grade 7</option>
                  <option value="8">Grade 8</option>
                  <option value="9">Grade 9</option>
                  <option value="10">Grade 10</option>
                </select>
              </div>
            </div>
            <ul className="subject-list">
              {subjects.map(subject => <li key={subject}>{subject}</li>)}
            </ul>
          </div>

          {/* === NEW NOTES CARD ADDED HERE === */}
          <div className="dashboard-card card-notes">
            <div className="neu-icon">
              <FaFileAlt />
            </div>
            <h2>Auto-Generated Notes</h2>
            <p>View your personalized notes, study guides, and video summaries.</p>
            <button className="neu-button">View My Notes</button>
          </div>


          {/* Bottom Row for Quiz/Homework */}
          <div className="bottom-card-row">
            <div className="dashboard-card card-quiz">
              <div className="neu-icon">
                <FaEdit />
              </div>
              <h2>Adaptive Quiz</h2>
              <p>Test your knowledge based on your strengths and weaknesses.</p>
              <button className="neu-button">Start Quiz</button>
            </div>

            <div className="dashboard-card card-homework">
              <div className="neu-icon">
                <FaUpload />
              </div>
              <h2>Homework Helper</h2>
              <p>Scan or upload your homework for AI-powered assistance.</p>
              <button className="neu-button">Upload/Scan</button>
            </div>
          </div>
        </main>

        {/* --- SIDEBAR (RIGHT) --- */}
        <aside className="dashboard-sidebar">
          
          {/* Syllabus Card (UPDATED) */}
          <div className="dashboard-card card-syllabus">
            <h2>Syllabus Covered</h2>
            <div className="chart-placeholder">
              <img 
                src={pieChartImage} 
                alt="Syllabus Pie Chart" 
                className="syllabus-pie-chart"
              />
            </div>
            <p className="chart-subtext">Hover a slice to see details.</p>
          </div>

          {/* Quote Card (Elongated) */}
          <div className="dashboard-card card-quote">
            <FaQuoteLeft className="quote-icon" />
            <p className="quote-text">The only way to do great work is to love what you do.</p>
            <span className="quote-author">- Steve Jobs</span>
          </div>

        </aside>

      </div>
    </div>
  );
};

export default Dashboard;
// src/App.jsx
import Welcome from "./pages/Welcome";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Chat from "./pages/Chat";
import Homework from "./pages/Homework";
import Quiz from "./pages/Quiz";
import Progress from "./pages/Progress";
import Planner from "./pages/Planner";
import Notes from "./pages/Notes";
import Reports from "./pages/Reports";

<Routes>
    <Route path="/" element={<Welcome />} />
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="/chat" element={<Chat />} />
    <Route path="/homework" element={<Homework />} />
    <Route path="/quiz" element={<Quiz />} />
    <Route path="/progress" element={<Progress />} />
    <Route path="/planner" element={<Planner />} />
    <Route path="/notes" element={<Notes />} />
    <Route path="/reports" element={<Reports />} />
</Routes>
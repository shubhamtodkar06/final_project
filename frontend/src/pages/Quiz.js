// src/pages/Quiz.jsx
import { useState } from "react";
import API from "../api/axios";

function Quiz() {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState([]);

  const generateQuiz = async () => {
    const res = await API.post("/api/quiz/generate/", {
      filters: { subjects: ["Math"], topics: ["Fractions"] },
      include_suggestions: true,
    });

    setQuiz(res.data);
  };

  const submitQuiz = async () => {
    const res = await API.post(`/api/quiz/${quiz.quiz_id}/submit/`, {
      answers,
    });

    alert("Score: " + res.data.score);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Quiz</h2>

        <button className="neu-button" onClick={generateQuiz}>
          Generate Quiz
        </button>

        {quiz &&
          quiz.questions.map((q, i) => (
            <div key={i}>
              <p>{q.q}</p>
              {q.options.map((opt, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    const newAns = [...answers];
                    newAns[i] = opt;
                    setAnswers(newAns);
                  }}
                >
                  {opt}
                </button>
              ))}
            </div>
          ))}

        {quiz && (
          <button className="neu-button" onClick={submitQuiz}>
            Submit
          </button>
        )}
      </div>
    </div>
  );
}

export default Quiz;
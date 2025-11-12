import React from "react";
import { useNavigate } from "react-router-dom";
import "../style.css"; // keep your neumorphic CSS

const Index = () => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        background: "#e0e5ec",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* --- Background Glow Effects --- */}
      <div
        style={{
          position: "absolute",
          top: "-120px",
          left: "-120px",
          width: "360px",
          height: "360px",
          background:
            "radial-gradient(circle at top left, rgba(255,255,255,0.8), #e0e5ec)",
          filter: "blur(100px)",
          zIndex: 0,
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-150px",
          right: "-150px",
          width: "460px",
          height: "460px",
          background:
            "radial-gradient(circle at bottom right, #bec3cf, #e0e5ec)",
          filter: "blur(140px)",
          zIndex: 0,
        }}
      />

      {/* --- Main Card --- */}
      <div
        className="login-card"
        style={{
          position: "relative",
          zIndex: 1,
          width: "95%",
          maxWidth: "550px",
          background: "#e0e5ec",
          borderRadius: "50px",
          padding: "80px 50px",
          textAlign: "center",
          boxShadow: "25px 25px 70px #bec3cf, -25px -25px 70px #ffffff",
          transition: "all 0.4s ease",
        }}
        onMouseEnter={(e) =>
          (e.currentTarget.style.boxShadow =
            "15px 15px 35px #bec3cf, -15px -15px 35px #ffffff")
        }
        onMouseLeave={(e) =>
          (e.currentTarget.style.boxShadow =
            "25px 25px 70px #bec3cf, -25px -25px 70px #ffffff")
        }
      >
        {/* --- User Icon --- */}
        <div
          style={{
            width: "130px",
            height: "130px",
            margin: "0 auto 35px",
            borderRadius: "50%",
            background: "#e0e5ec",
            boxShadow:
              "10px 10px 20px #bec3cf, -10px -10px 20px #ffffff, inset 0 0 0 #bec3cf, inset 0 0 0 #ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            stroke="#6c7293"
            strokeWidth="1.8"
            viewBox="0 0 24 24"
            width="70"
            height="70"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 12c2.485 0 4.5-2.015 4.5-4.5S14.485 3 12 3 7.5 5.015 7.5 7.5 9.515 12 12 12zm0 0c-4.142 0-7.5 2.239-7.5 5v1.5a.5.5 0 00.5.5h14a.5.5 0 00.5-.5V17c0-2.761-3.358-5-7.5-5z"
            />
          </svg>
        </div>

        {/* --- Heading --- */}
        <h1
          style={{
            fontSize: "2.8rem",
            fontWeight: "700",
            color: "#3d4468",
            marginBottom: "12px",
            letterSpacing: "0.5px",
          }}
        >
          Welcome
        </h1>

        <p
          style={{
            color: "#80849b",
            fontSize: "17px",
            marginBottom: "55px",
            fontWeight: "500",
          }}
        >
          Sign in or create your account to get started
        </p>

        {/* --- Buttons --- */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "30px",
          }}
        >
          {/* Login Button */}
          <button
            className="neu-button"
            onClick={() => navigate("/login")}
            style={{
              fontSize: "18px",
              fontWeight: "600",
              border: "none",
              outline: "none",
              borderRadius: "20px",
              padding: "18px 26px",
              background: "#e0e5ec",
              color: "#3d4468",
              cursor: "pointer",
              transition: "all 0.3s ease",
              boxShadow:
                "10px 10px 25px #bec3cf, -10px -10px 25px #ffffff",
            }}
            onMouseEnter={(e) =>
              (e.target.style.boxShadow =
                "inset 6px 6px 14px #bec3cf, inset -6px -6px 14px #ffffff")
            }
            onMouseLeave={(e) =>
              (e.target.style.boxShadow =
                "10px 10px 25px #bec3cf, -10px -10px 25px #ffffff")
            }
          >
            Login
          </button>

          {/* Register Button */}
          <button
            className="neu-button"
            onClick={() => navigate("/register")}
            style={{
              fontSize: "18px",
              fontWeight: "600",
              border: "none",
              outline: "none",
              borderRadius: "20px",
              padding: "18px 26px",
              background: "#e0e5ec",
              color: "#3d4468",
              cursor: "pointer",
              transition: "all 0.3s ease",
              boxShadow:
                "10px 10px 25px #bec3cf, -10px -10px 25px #ffffff",
            }}
            onMouseEnter={(e) =>
              (e.target.style.boxShadow =
                "inset 6px 6px 14px #bec3cf, inset -6px -6px 14px #ffffff")
            }
            onMouseLeave={(e) =>
              (e.target.style.boxShadow =
                "10px 10px 25px #bec3cf, -10px -10px 25px #ffffff")
            }
          >
            Register
          </button>
        </div>
      </div>

      {/* --- Subtle Glow Pulse Animation --- */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: "700px",
          height: "700px",
          transform: "translate(-50%, -50%)",
          background:
            "radial-gradient(circle, rgba(255,255,255,0.25), transparent 75%)",
          filter: "blur(120px)",
          zIndex: "-1",
          animation: "pulseGlow 6s ease-in-out infinite alternate",
        }}
      ></div>

      <style>{`
        @keyframes pulseGlow {
          from { opacity: 0.6; transform: translate(-50%, -50%) scale(1); }
          to { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
        }
      `}</style>
    </div>
  );
};

export default Index;

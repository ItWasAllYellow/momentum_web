import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Landing.css';

const Landing = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [loginId, setLoginId] = useState("");
    const [loginPw, setLoginPw] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [refreshStatus, setRefreshStatus] = useState("");

    // Trigger data refresh in background
    const triggerDataRefresh = async () => {
        try {
            setRefreshStatus("📊 데이터 갱신 중...");
            const response = await fetch('http://localhost:8000/api/data/refresh', {
                method: 'POST'
            });
            const data = await response.json();

            if (data.status === 'success') {
                setRefreshStatus("✅ 데이터 갱신 완료!");
            } else {
                setRefreshStatus("⚠️ 일부 데이터 갱신 실패");
            }

            // Clear status after 3 seconds
            setTimeout(() => setRefreshStatus(""), 3000);
        } catch (err) {
            console.error("Data refresh error:", err);
            setRefreshStatus("❌ 데이터 갱신 오류");
            setTimeout(() => setRefreshStatus(""), 3000);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        const endpoint = isLogin ? 'http://localhost:8000/api/login' : 'http://localhost:8000/api/signup';

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: loginId, password: loginPw })
            });
            const data = await response.json();

            if (data.status === 'success') {
                if (isLogin) {
                    login(data.user, data.token);

                    // Check if data refresh is needed
                    if (data.needs_refresh) {
                        // Trigger refresh in background (don't wait)
                        triggerDataRefresh();
                    }

                    navigate('/mode');
                } else {
                    alert("회원가입 성공! 로그인해주세요.");
                    setIsLogin(true);
                }
            } else {
                setError(data.message || "오류가 발생했습니다.");
            }
        } catch (err) {
            console.error("Login/Signup Error:", err);
            setError(`서버 연결 오류: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="landing-page">
            {/* Data refresh toast notification */}
            {refreshStatus && (
                <div className="refresh-toast">
                    {refreshStatus}
                </div>
            )}

            <div className="landing-content">
                <div className="brand-container">
                    <h1 className="brand-title animate-title">Momentum</h1>
                    <div className="brand-glow"></div>
                </div>
                <p className="brand-subtitle">
                    흐름을 읽어내는 당신의 스마트한 투자 파트너
                </p>

                <div className="login-box card">
                    <h2>{isLogin ? "로그인" : "회원가입"}</h2>
                    <form onSubmit={handleSubmit}>
                        <input
                            type="text"
                            placeholder="ID"
                            value={loginId}
                            onChange={(e) => setLoginId(e.target.value)}
                            className="login-input"
                            disabled={isLoading}
                        />
                        <input
                            type="password"
                            placeholder="Password"
                            value={loginPw}
                            onChange={(e) => setLoginPw(e.target.value)}
                            className="login-input"
                            disabled={isLoading}
                        />
                        {error && <p className="error-msg">{error}</p>}
                        <button
                            type="submit"
                            className="btn btn-primary login-btn"
                            disabled={isLoading}
                        >
                            {isLoading ? "처리 중..." : (isLogin ? "로그인" : "가입하기")}
                        </button>
                    </form>
                    <div className="toggle-auth">
                        <button onClick={() => setIsLogin(!isLogin)} className="text-btn" disabled={isLoading}>
                            {isLogin ? "계정이 없으신가요? 회원가입" : "이미 계정이 있으신가요? 로그인"}
                        </button>
                    </div>
                    {isLogin && (
                        <div className="demo-hint">
                            Test ID: 20201651 / PW: 20201651
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Landing;

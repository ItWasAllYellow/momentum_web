import React from 'react';
import { useNavigate } from 'react-router-dom';
import './Landing.css'; // Reuse landing styles for cards

const ModeSelection = () => {
    const navigate = useNavigate();
    const user = localStorage.getItem('user');

    return (
        <div className="landing-page">
            <div className="landing-content">
                <h1 className="brand-title" style={{ fontSize: '3rem', marginBottom: '10px' }}>Welcome, {user}</h1>
                <p className="brand-subtitle">Select your investment mode</p>

                <div className="mode-cards">
                    <div className="card mode-card" onClick={() => navigate('/easy')}>
                        <div className="icon">🌱</div>
                        <h3>Easy Mode</h3>
                        <p>대가의 조언과 함께하는<br />쉬운 포트폴리오 관리</p>
                    </div>

                    <div className="card mode-card" onClick={() => navigate('/expert')}>
                        <div className="icon">📈</div>
                        <h3>Expert Mode</h3>
                        <p>심층 데이터와 톤 분석으로<br />시장 흐름 파악</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ModeSelection;

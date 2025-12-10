import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import './Navbar.css';

const Navbar = ({ mode }) => {
    const navigate = useNavigate();

    return (
        <nav className="navbar">
            <div className="container navbar-content">
                <Link to="/" className="logo">
                    Momentum <span className="mode-badge">{mode === 'easy' ? 'AI Assistant' : 'Pro Insight'}</span>
                </Link>

                <div className="nav-links">
                    <button
                        className={`nav-btn ${mode === 'easy' ? 'active' : ''}`}
                        onClick={() => navigate('/easy')}
                    >
                        Easy Mode
                    </button>
                    <button
                        className={`nav-btn ${mode === 'expert' ? 'active' : ''}`}
                        onClick={() => navigate('/expert')}
                    >
                        Expert Mode
                    </button>
                    <div className="user-profile">
                        <div className="avatar">U</div>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;

import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
    const { user } = useAuth();

    // Also check localStorage for persistence across refreshes
    const storedUser = localStorage.getItem('user');

    if (!user && !storedUser) {
        return <Navigate to="/" replace />;
    }

    return children;
};

export default ProtectedRoute;

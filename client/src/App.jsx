import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import ModeSelection from './pages/ModeSelection';
import EasyMode from './pages/EasyMode';
import ExpertMode from './pages/ExpertMode';
import Navbar from './components/Navbar';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="app">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route
              path="/mode"
              element={
                <ProtectedRoute>
                  <ModeSelection />
                </ProtectedRoute>
              }
            />
            <Route
              path="/easy"
              element={
                <ProtectedRoute>
                  <Navbar mode="easy" />
                  <EasyMode />
                </ProtectedRoute>
              }
            />
            <Route
              path="/expert"
              element={
                <ProtectedRoute>
                  <Navbar mode="expert" />
                  <ExpertMode />
                </ProtectedRoute>
              }
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;

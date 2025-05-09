import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useMatch } from 'react-router-dom';
import AgentList from './components/AgentList';
import AgentResolver from './components/AgentResolver';
import AgentRegistration from './components/AgentRegistration';
import ansService from './api/ansService';
import './App.css';

// Custom Nav Link component to highlight active links
const NavLink = ({ to, children }: { to: string; children: React.ReactNode }) => {
  const match = useMatch(to);
  return (
    <Link to={to} className={match ? 'active' : ''}>
      {children}
    </Link>
  );
};

const App: React.FC = () => {
  const [serverStatus, setServerStatus] = useState<'loading' | 'online' | 'offline'>('loading');
  
  useEffect(() => {
    const checkServerStatus = async () => {
      try {
        await ansService.checkHealth();
        setServerStatus('online');
      } catch (error) {
        console.error('Server health check failed:', error);
        setServerStatus('offline');
      }
    };
    
    checkServerStatus();
  }, []);
  
  return (
    <Router>
      <div className="app">
        <header>
          <div className="container">
            <h1>Agent Name Service (ANS) Dashboard</h1>
            <div className="server-status">
              Server: <span className={`status-${serverStatus}`}>
                {serverStatus === 'loading' ? 'Checking...' : serverStatus}
              </span>
            </div>
          </div>
        </header>
        
        <nav>
          <div className="container">
            <ul>
              <li><NavLink to="/">Agent Directory</NavLink></li>
              <li><NavLink to="/resolve">Resolve Agent</NavLink></li>
              <li><NavLink to="/register">Register Agent</NavLink></li>
            </ul>
          </div>
        </nav>
        
        <main className="container">
          {serverStatus === 'offline' ? (
            <div className="server-offline-warning">
              <h2>Server Offline</h2>
              <p>The ANS server appears to be offline. Please ensure it is running at http://localhost:8000</p>
              <button onClick={() => setServerStatus('loading')}>Retry Connection</button>
            </div>
          ) : (
            <Routes>
              <Route path="/" element={<AgentList />} />
              <Route path="/resolve" element={<AgentResolver />} />
              <Route path="/register" element={<AgentRegistration />} />
            </Routes>
          )}
        </main>
        
        <footer>
          <div className="container">
            <p>Agent Name Service (ANS) Dashboard</p>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App; 
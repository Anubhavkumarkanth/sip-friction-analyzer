import { FC, useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import MonteCarlo from './pages/MonteCarlo';
import FundExplorer from './pages/FundExplorer';
import CompareFunds from './pages/CompareFunds';
import Login from './pages/Login';
import ErrorBoundary from './components/ui/ErrorBoundary';
import { authAPI, UNAUTHORIZED_EVENT } from './services/api';
import './App.css';

const App: FC = () => {
  const [loggedIn, setLoggedIn] = useState<boolean>(() => authAPI.isLoggedIn());

  // The API layer clears an expired token and fires this event. Without it the
  // app would keep rendering as though signed in while every request failed.
  useEffect(() => {
    const handleUnauthorized = (): void => setLoggedIn(false);
    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

  // With no session, try the shared demo account first. A server with demo mode
  // off answers 404 and the sign-in page below is shown as before.
  const [checkingDemo, setCheckingDemo] = useState<boolean>(() => !authAPI.isLoggedIn());
  useEffect(() => {
    if (loggedIn) return;
    let cancelled = false;
    setCheckingDemo(true);
    authAPI.demoLogin().then((ok) => {
      if (cancelled) return;
      if (ok) setLoggedIn(true);
      setCheckingDemo(false);
    });
    return () => {
      cancelled = true;
    };
  }, [loggedIn]);

  if (!loggedIn && checkingDemo) {
    return <p role="status" style={{ padding: '2rem' }}>Loading…</p>;
  }

  if (!loggedIn) {
    return (
      <ErrorBoundary>
        <Login onSuccess={() => setLoggedIn(true)} />
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="monte-carlo" element={<MonteCarlo />} />
            <Route path="funds" element={<FundExplorer />} />
            <Route path="compare" element={<CompareFunds />} />
          </Route>
        </Routes>
      </Router>
    </ErrorBoundary>
  );
};

export default App;

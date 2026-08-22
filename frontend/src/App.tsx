import { FC } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import MonteCarlo from './pages/MonteCarlo';
import FundExplorer from './pages/FundExplorer';
import CompareFunds from './pages/CompareFunds';
import ErrorBoundary from './components/ui/ErrorBoundary';
import './App.css';

const App: FC = () => {
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

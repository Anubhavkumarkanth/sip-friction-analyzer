import React from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { TrendingUp, Activity, Search, BarChart2 } from 'lucide-react';
import './AppLayout.css';

const AppLayout = () => {
  const location = useLocation();
  
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard Overview';
      case '/monte-carlo': return 'Monte Carlo Simulator';
      case '/funds': return 'Fund Explorer';
      case '/compare': return 'Compare Funds';
      default: return 'Overview';
    }
  };

  return (
    <div className="app-layout">
      <aside className="sidebar glass-panel">
        <div className="sidebar-header">
          <TrendingUp className="logo-icon" size={32} />
          <h2 className="text-gradient">SipFriction</h2>
        </div>
        
        <nav className="sidebar-nav">
          <NavLink to="/" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <BarChart2 size={20} />
            <span>Dashboard</span>
          </NavLink>
          <NavLink to="/monte-carlo" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <Activity size={20} />
            <span>Monte Carlo</span>
          </NavLink>
          <NavLink to="/funds" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            <Search size={20} />
            <span>Funds Explorer</span>
          </NavLink>
        </nav>
        
        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="avatar">A</div>
            <div>
              <p className="user-name">Pro Investor</p>
              <p className="user-status text-gradient">Ready</p>
            </div>
          </div>
        </div>
      </aside>
      
      <main className="main-content-area">
        <header className="top-header glass-panel">
          <div className="header-title">
            <h3>{getPageTitle()}</h3>
          </div>
          <div className="header-actions">
            <button className="icon-btn hover-scale"><Search size={20} /></button>
          </div>
        </header>
        
        <div className="page-content animate-fade-in">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AppLayout;

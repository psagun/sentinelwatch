import { useState } from 'react';
import { Routes, Route, useNavigate, useLocation, Link } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Findings from './pages/Findings';
import Alerts from './pages/Alerts';
import Entities from './pages/Entities';
import About from './pages/About';
import Compliance from './pages/Compliance';
import Hackathon from './pages/Hackathon';
import Reports from './pages/Reports';
import { ToastProvider } from './components/Toast';
import ErrorBoundary from './components/ErrorBoundary';
import type { NavPage } from './types';

export default function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const pageMap: Record<string, NavPage> = {
    '/': 'dashboard',
    '/findings': 'findings',
    '/alerts': 'alerts',
    '/entities': 'entities',
    '/about': 'about',
    '/hackathon': 'hackathon',
    '/compliance': 'compliance',
    '/reports': 'reports',
  };

  const activePage: NavPage = pageMap[location.pathname] || 'dashboard';

  const handleNavigate = (page: NavPage) => {
    const pathMap: Record<NavPage, string> = {
      dashboard: '/',
      findings: '/findings',
      alerts: '/alerts',
      entities: '/entities',
      compliance: '/compliance',
      reports: '/reports',
      about: '/about',
      hackathon: '/hackathon',
    };
    navigate(pathMap[page]);
  };

  return (
    <ErrorBoundary>
      <ToastProvider>
        <Layout activePage={activePage} onNavigate={handleNavigate}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/entities" element={<Entities />} />
            <Route path="/about" element={<About />} />
            <Route path="/hackathon" element={<Hackathon />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/reports" element={<Reports />} />
            <Route
              path="*"
              element={
                <div className="flex items-center justify-center min-h-[320px] p-8">
                  <div className="widget max-w-md w-full text-center">
                    <div className="mb-4 inline-flex items-center justify-center w-12 h-12 rounded-full bg-accent-cyan/10">
                      <svg className="w-6 h-6 text-accent-cyan" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm0 2a1 1 0 00-1 1v5a1 1 0 002 0V3a1 1 0 00-1-1zm0 8a1 1 0 100 2 1 1 0 000-2z" />
                      </svg>
                    </div>
                    <h2 className="text-base font-semibold text-text-primary mb-1">Page not found</h2>
                    <p className="text-sm text-text-muted mb-6">
                      The page you are looking for does not exist.
                    </p>
                    <Link
                      to="/"
                      className="inline-block px-5 py-2 rounded-lg text-sm font-medium bg-accent-cyan/10 text-accent-cyan
                                 border border-accent-cyan/20 hover:bg-accent-cyan/20 transition-colors"
                    >
                      Back to Dashboard
                    </Link>
                  </div>
                </div>
              }
            />
          </Routes>
        </Layout>
      </ToastProvider>
    </ErrorBoundary>
  );
}

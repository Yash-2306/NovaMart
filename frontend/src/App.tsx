import { useState, useCallback, useEffect } from 'react';
import ChatWindow from './components/ChatWindow';
import AdminDashboard from './components/AdminDashboard';
import PolicyViewer from './components/PolicyViewer';
import CustomersPanel from './components/CustomersPanel';
import CustomerDetails from './components/CustomerDetails';
import type { StepEvent } from './types';

export default function App() {
  const [liveSteps, setLiveSteps] = useState<StepEvent[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'admin' | 'policy' | 'customers'>(() => {
    return (localStorage.getItem('novamart_active_tab') as any) || 'chat';
  });
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(() => {
    return localStorage.getItem('novamart_selected_customer');
  });
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'unhealthy'>('healthy');
  
  // Theme switcher state
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem('novamart_theme');
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  const handleStepsUpdate = useCallback((steps: StepEvent[]) => {
    setLiveSteps(steps);
  }, []);

  useEffect(() => {
    const root = window.document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('novamart_theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('novamart_active_tab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (selectedCustomerId) {
      localStorage.setItem('novamart_selected_customer', selectedCustomerId);
    } else {
      localStorage.removeItem('novamart_selected_customer');
    }
  }, [selectedCustomerId]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch('/api/health');
        if (res.ok) {
          const data = await res.json();
          setHealthStatus(data.status);
        } else {
          setHealthStatus('unhealthy');
        }
      } catch (err) {
        setHealthStatus('unhealthy');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <div className="h-screen flex overflow-hidden bg-slate-50 dark:bg-zinc-950 text-slate-800 dark:text-zinc-200 transition-colors">
      {/* Sidebar navigation */}
      <aside className="w-64 flex-shrink-0 bg-white dark:bg-black border-r border-slate-200 dark:border-zinc-800 flex flex-col justify-between transition-colors shadow-[4px_0_24px_rgba(0,0,0,0.02)] dark:shadow-[4px_0_24px_rgba(255,255,255,0.02)] z-20">
        <div className="flex-1 flex flex-col pt-6 pb-4 overflow-y-auto">
          {/* Logo / Brand */}
          <div className="flex items-center gap-3 px-5 mb-8">
            <div className="w-8 h-8 rounded-lg bg-slate-900 dark:bg-zinc-100 flex items-center justify-center shadow-sm">
              <svg className="w-4 h-4 text-white dark:text-black" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
                NovaMart
              </h1>
              <p className="text-[10px] text-slate-500 dark:text-zinc-400 font-semibold uppercase tracking-wider">
                Support Console
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 px-3 space-y-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`w-full nav-item ${activeTab === 'chat' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
              </svg>
              <span>Live Chat</span>
            </button>

            <button
              onClick={() => setActiveTab('admin')}
              className={`w-full nav-item ${activeTab === 'admin' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              <span>Analytics & Replays</span>
            </button>

            <button
              onClick={() => setActiveTab('policy')}
              className={`w-full nav-item ${activeTab === 'policy' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Refund Rules Engine</span>
            </button>

            <button
              onClick={() => setActiveTab('customers')}
              className={`w-full nav-item ${activeTab === 'customers' ? 'active' : ''}`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <span>Customers Directory</span>
            </button>
          </nav>
        </div>

        {/* Footer Info & Health status */}
        <div className="p-4 border-t border-slate-200 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-950/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${
                healthStatus === 'healthy' ? 'bg-emerald-500' : 
                healthStatus === 'degraded' ? 'bg-amber-500' : 'bg-red-500'
              }`} />
              <span className="text-[10px] font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-wider">
                System Status
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-600 dark:text-zinc-400 font-semibold uppercase">
              {healthStatus}
            </span>
          </div>
        </div>
      </aside>

      {/* Main body content area */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header bar */}
        <header className="h-14 flex-shrink-0 border-b border-slate-200 dark:border-zinc-800 flex items-center justify-between px-6 bg-white dark:bg-black shadow-sm transition-colors">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-zinc-400">
            <span className="font-medium">Console</span>
            <span>/</span>
            <span className="font-semibold text-slate-800 dark:text-zinc-200">
              {activeTab === 'chat' ? 'Live Support Conversation' : activeTab === 'admin' ? 'Agent Analytics & Dashboard' : activeTab === 'customers' ? 'Customers Directory' : 'Configured Store Policies'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {/* Theme Toggle Button */}
            <button 
              onClick={toggleTheme} 
              className="p-1.5 rounded-lg border border-slate-200 dark:border-zinc-800 text-slate-500 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-zinc-900 transition-colors"
              title="Toggle theme mode"
            >
              {theme === 'light' ? (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              ) : (
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728A9 9 0 115.636 5.636a9 9 0 0112.728 12.728z" />
                </svg>
              )}
            </button>
            <div className="text-[11px] text-slate-600 dark:text-zinc-400 font-medium bg-slate-100 dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 px-2.5 py-1 rounded">
              v1.4.0
            </div>
          </div>
        </header>

        {/* Dynamic Inner Panel View */}
        <div className="flex-1 overflow-hidden relative">
          <div className={`h-full max-w-4xl mx-auto flex flex-col w-full px-4 ${activeTab === 'chat' ? '' : 'hidden'}`}>
            <div className="flex-1 overflow-hidden my-4 bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm flex flex-col transition-colors">
              <ChatWindow onStepsUpdate={handleStepsUpdate} active={activeTab === 'chat'} />
            </div>
          </div>
          
          <div className={`h-full flex flex-col w-full ${activeTab === 'admin' ? '' : 'hidden'}`}>
            <AdminDashboard liveSteps={liveSteps} />
          </div>

          <div className={`h-full max-w-4xl mx-auto flex flex-col w-full my-4 px-4 overflow-hidden bg-white dark:bg-black border border-slate-200 dark:border-zinc-800 rounded-xl shadow-sm transition-colors ${activeTab === 'policy' ? '' : 'hidden'}`}>
            <PolicyViewer />
          </div>
          
          <div className={`h-full flex flex-col w-full ${activeTab === 'customers' ? '' : 'hidden'}`}>
            {selectedCustomerId ? (
              <CustomerDetails customerId={selectedCustomerId} onBack={() => setSelectedCustomerId(null)} />
            ) : (
              <CustomersPanel onViewCustomer={setSelectedCustomerId} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

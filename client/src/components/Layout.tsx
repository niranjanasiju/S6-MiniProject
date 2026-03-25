import { Link, Outlet, useLocation } from 'react-router-dom';
import { Activity } from 'lucide-react';

const Layout = () => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';
  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-200 selection:bg-cyan-500/30">
      <nav className="sticky top-0 z-50 w-full border-b border-slate-800/50 bg-slate-950/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-2">
              <div className="p-2 bg-gradient-to-br from-cyan-500 to-emerald-500 rounded-lg">
                <Activity className="h-5 w-5 text-slate-950" />
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                MedSafe AI
              </span>
            </Link>
            <div className="hidden md:block">
              <div className="ml-10 flex items-baseline space-x-4">
                <Link to="/polypharmacy" className="px-3 py-2 rounded-md text-sm font-medium hover:text-cyan-400 transition-colors">
                  Polypharmacy
                </Link>
                <Link to="/adr" className="px-3 py-2 rounded-md text-sm font-medium hover:text-emerald-400 transition-colors">
                  ADR Predictor
                </Link>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="flex-grow w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {!isLandingPage && (
        <footer className="w-full border-t border-slate-800/50 py-6 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 gap-2 flex flex-col sm:flex-row justify-center items-center text-center sm:text-left text-sm text-slate-500">
            <Activity className="h-4 w-4 text-slate-600 hidden sm:block" />
            <p>
              <span className="font-semibold text-slate-400">Disclaimer:</span> The model may make mistakes, do consult a professional doctor.
            </p>
          </div>
        </footer>
      )}
    </div>
  );
};

export default Layout;

import { Link, Outlet } from 'react-router-dom';
import { Activity } from 'lucide-react';

const Layout = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 selection:bg-cyan-500/30">
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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 h-full">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;

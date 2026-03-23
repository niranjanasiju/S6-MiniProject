import { motion } from 'framer-motion';
import { ArrowRight, Activity, ShieldAlert } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: 'spring' as const, stiffness: 300, damping: 24 } }
};

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh]">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="w-full max-w-5xl"
      >
        <div className="text-center mb-16 relative">
          <div className="absolute top-1/2 left-1/2 -z-10 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-500/20 blur-[120px]"></div>
          
          <motion.h1 variants={itemVariants} className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6">
            Predict & Prevent <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-emerald-400">
              Adverse Drug Events
            </span>
          </motion.h1>
          <motion.p variants={itemVariants} className="mt-4 max-w-2xl mx-auto text-xl text-slate-400">
            Advanced AI models trained on millions of clinical records to identify dangerous interactions and side effects before they occur.
          </motion.p>
        </div>

        <motion.div variants={itemVariants} className="grid md:grid-cols-2 gap-8">
          
          {/* Polypharmacy Module Card */}
          <div 
            onClick={() => navigate('/polypharmacy')}
            className="group relative cursor-pointer overflow-hidden rounded-2xl bg-slate-900/50 border border-slate-800 p-8 pt-10 hover:border-cyan-500/50 transition-colors backdrop-blur-sm"
          >
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Activity className="w-32 h-32 text-cyan-400" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-cyan-400/10 text-cyan-400 mb-6 group-hover:scale-110 transition-transform">
                <Activity className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">Polypharmacy Check</h2>
              <p className="text-slate-400 mb-8 min-h-[3rem]">
                Evaluate the safety of adding new medications to an existing patient regimen.
              </p>
              <div className="flex items-center text-cyan-400 font-medium">
                Try Predictor <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

          {/* ADR Module Card */}
          <div 
            onClick={() => navigate('/adr')}
            className="group relative cursor-pointer overflow-hidden rounded-2xl bg-slate-900/50 border border-slate-800 p-8 pt-10 hover:border-emerald-500/50 transition-colors backdrop-blur-sm"
          >
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <ShieldAlert className="w-32 h-32 text-emerald-400" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-emerald-400/10 text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-3">ADR Profiling</h2>
              <p className="text-slate-400 mb-8 min-h-[3rem]">
                Predict potential side effects and target pathways for individual drugs.
              </p>
              <div className="flex items-center text-emerald-400 font-medium">
                Analyze Drug <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </div>
          </div>

        </motion.div>
      </motion.div>
    </div>
  );
};

export default Landing;

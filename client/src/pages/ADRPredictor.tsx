import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, Loader2, ActivitySquare, BrainCircuit, Activity, ShieldAlert, HeartPulse, Eye, Dna, Ear } from 'lucide-react';
import { predictADR, searchADRDrugs } from '../api';
import type { ADRResponse, ADRSideEffect } from '../types';
import Autocomplete from '../components/Autocomplete';

const CategoryIcon = ({ category }: { category: string }) => {
  const norm = category.toLowerCase();
  if (norm.includes('cardiac') || norm.includes('heart')) return <HeartPulse className="w-5 h-5 text-rose-400" />;
  if (norm.includes('nervous') || norm.includes('brain') || norm.includes('psych')) return <BrainCircuit className="w-5 h-5 text-purple-400" />;
  if (norm.includes('gastro')) return <Activity className="w-5 h-5 text-yellow-400" />;
  if (norm.includes('eye') || norm.includes('vision') || norm.includes('opthal')) return <Eye className="w-5 h-5 text-cyan-400" />;
  if (norm.includes('ear') || norm.includes('hearing')) return <Ear className="w-5 h-5 text-indigo-400" />;
  if (norm.includes('metabolism') || norm.includes('endo') || norm.includes('blood')) return <Dna className="w-5 h-5 text-emerald-400" />;
  if (norm.includes('musculo')) return <Activity className="w-5 h-5 text-orange-400" />;
  return <ShieldAlert className="w-5 h-5 text-slate-400" />;
};

export default function ADRPredictor() {
  const [drugName, setDrugName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ADRResponse | null>(null);

  const fetchSuggestions = async (q: string) => {
    try {
      const res = await searchADRDrugs(q);
      return res.matches;
    } catch {
      return [];
    }
  };

  const handleAnalyze = async () => {
    const drugToAnalyze = drugName.trim();
    if (!drugToAnalyze) {
      setError("Please search and select a drug.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await predictADR({
        drug_name: drugToAnalyze,
        threshold: 0.5
      });
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to analyze drug.");
    } finally {
      setLoading(false);
    }
  };

  const groupedEffects = useMemo(() => {
    if (!result) return {};
    return result.side_effects.reduce((acc, curr) => {
      if (!acc[curr.category]) acc[curr.category] = [];
      acc[curr.category].push(curr);
      return acc;
    }, {} as Record<string, ADRSideEffect[]>);
  }, [result]);

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Adverse Drug Reaction Profiling</h1>
        <p className="text-slate-400">Analyze a single drug's potential side effects and targeted biological pathways.</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Left Col: Form */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
            <label className="block text-sm font-medium text-slate-300 mb-2">Search Database</label>
            <div className="mb-6">
              <Autocomplete
                value={drugName}
                onChange={setDrugName}
                fetchSuggestions={fetchSuggestions}
                placeholder="Search drug (e.g. atorvastatin)..."
              />
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading || !drugName}
              className="w-full bg-emerald-500 hover:bg-emerald-400 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
            >
              {loading ? (
                <><Loader2 className="animate-spin h-5 w-5 mr-2" /> Profiling...</>
              ) : "Generate Profile"}
            </button>
            
            {error && (
              <div className="mt-4 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
                {error}
              </div>
            )}
          </div>
          
          {/* Active Result Sidebar info */}
          {result && (
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-6"
            >
              <h3 className="text-lg font-medium text-white flex items-center mb-4">
                <BrainCircuit className="w-5 h-5 mr-2 text-emerald-400" /> Pathways Reached
              </h3>
              {result.pathways.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {result.pathways.map(p => (
                    <span key={p} className="px-2.5 py-1.5 bg-slate-950 text-xs text-slate-300 rounded-md border border-slate-800 font-medium">
                      {p}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No pathways dynamically documented.</p>
              )}

              <h3 className="text-lg font-medium text-white flex items-center mb-4 mt-8">
                <ActivitySquare className="w-5 h-5 mr-2 text-cyan-400" /> Targets
              </h3>
              {result.targets.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {result.targets.map(t => (
                    <span key={t} className="px-2.5 py-1.5 bg-cyan-950/30 text-xs text-cyan-400 rounded-md border border-cyan-900/50 font-medium font-mono">
                      {t}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-500">No targets identified.</p>
              )}
            </motion.div>
          )}
        </div>

        {/* Right Col: Results */}
        <div className="lg:col-span-2">
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="results"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="space-y-6"
              >
                {/* AI Explanation */}
                <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 relative overflow-hidden">
                  <ActivitySquare className="absolute -right-4 -bottom-4 w-32 h-32 text-emerald-500/10" />
                  <h2 className="text-xl font-bold text-white mb-5 relative z-10 flex items-center shadow-emerald-400/20 drop-shadow-lg">
                    AI Analysis: {result.drug.toUpperCase()}
                  </h2>
                  <div className="text-slate-300 leading-relaxed relative z-10 text-sm md:text-base space-y-5">
                    {typeof result.ai_explanation === 'object' && result.ai_explanation !== null ? (
                      <>
                        <div>
                          <span className="font-semibold text-cyan-400 block mb-1">What is it?</span>
                          <p>{result.ai_explanation.what_is_it}</p>
                        </div>
                        <div>
                          <span className="font-semibold text-emerald-400 block mb-1">What did we find?</span>
                          <p>{result.ai_explanation.what_did_we_find}</p>
                        </div>
                        <div>
                          <span className="font-semibold text-yellow-400 block mb-1">Side effects to watch for:</span>
                          <p>{result.ai_explanation.side_effects_to_watch}</p>
                        </div>
                        <div>
                          <span className="font-semibold text-emerald-400 block mb-1">Safe usage tips:</span>
                          <p>{result.ai_explanation.safe_usage_tips}</p>
                        </div>
                        <div>
                          <span className="font-semibold text-rose-400 block mb-1">When to call your doctor:</span>
                          <p>{result.ai_explanation.when_to_call_doctor}</p>
                        </div>
                      </>
                    ) : (
                      <p>{String(result.ai_explanation) || "No AI explanation generated."}</p>
                    )}
                  </div>
                </div>

                {/* Side Effects List */}
                <div className="flex items-center justify-between mt-8 mb-4">
                  <h3 className="text-xl font-semibold text-white">Clinical Side Effect Probabilities</h3>
                  <span className="text-xs text-slate-400 bg-slate-800 px-3 py-1 rounded-full border border-slate-700 font-medium">
                    Filter: {'>'} {(result.threshold * 100).toFixed(0)}% Risk
                  </span>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                  {Object.entries(groupedEffects).map(([category, effects]) => (
                    <div key={category} className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors shadow-lg">
                      <div className="flex items-center mb-4 pb-3 border-b border-slate-800">
                        <div className="p-2 bg-slate-950 rounded-lg">
                          <CategoryIcon category={category} />
                        </div>
                        <h4 className="font-semibold text-slate-200 ml-3 capitalize tracking-wide text-sm">
                          {category}
                        </h4>
                      </div>

                      <div className="space-y-4">
                        {effects.length > 0 ? (
                          effects.map((effect, i) => (
                            <div key={i} className="flex flex-col text-sm group">
                              <div className="flex justify-between items-center mb-1.5">
                                <span className="text-slate-300 capitalize text-xs font-medium group-hover:text-white transition-colors">
                                  {effect.effect}
                                </span>
                                <span className="text-xs font-mono font-bold" style={{ color: effect.probability > 90 ? '#f43f5e' : effect.probability > 75 ? '#eab308' : '#34d399' }}>
                                  {effect.probability.toFixed(1)}%
                                </span>
                              </div>
                              <div className="w-full h-1.5 bg-slate-950 py-px px-px rounded-full overflow-hidden">
                                <motion.div 
                                  initial={{ width: 0 }}
                                  animate={{ width: `${Math.min(100, effect.probability)}%` }}
                                  transition={{ duration: 0.8, delay: i * 0.1 }}
                                  className={`h-full rounded-full ${effect.probability > 90 ? 'bg-rose-500' : effect.probability > 75 ? 'bg-yellow-500' : 'bg-emerald-500'}`}
                                />
                              </div>
                            </div>
                          ))
                        ) : (
                          <span className="text-xs text-slate-500 italic block py-2">No effects exceeding threshold parameters.</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {Object.keys(groupedEffects).length === 0 && (
                    <div className="col-span-2 text-center text-slate-500 py-8 bg-slate-900/30 rounded-xl border border-slate-800">
                      No side effects exceeded the probability threshold.
                    </div>
                  )}
                </div>
              </motion.div>
            ) : (
              <div key="placeholder" className="h-full min-h-[400px] border border-slate-800/50 border-dashed rounded-2xl flex items-center justify-center p-12 text-center bg-slate-900/10">
                <p className="text-slate-500 flex flex-col items-center">
                  <Info className="w-8 h-8 mb-4 text-slate-600" />
                  Search and select a drug to reveal pathway interactions and organ-system effect predictions.
                </p>
              </div>
            )}
          </AnimatePresence>
        </div>
        
      </div>
    </div>
  );
}

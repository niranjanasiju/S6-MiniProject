import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, AlertTriangle, CheckCircle, Info, Loader2 } from 'lucide-react';
import { predictPolypharmacy, searchDrugs } from '../api';
import type { PredictResponse } from '../types';
import Autocomplete from '../components/Autocomplete';

export default function PolypharmacyPredictor() {
  const [newDrug, setNewDrug] = useState('');
  const [currentDrugs, setCurrentDrugs] = useState<string[]>([]);
  const [currentDrugInput, setCurrentDrugInput] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const fetchSuggestions = async (q: string) => {
    try {
      const res = await searchDrugs(q);
      return res.matches;
    } catch {
      return [];
    }
  };

  const handleAddCurrentDrug = () => {
    if (currentDrugInput.trim() && !currentDrugs.includes(currentDrugInput.trim())) {
      setCurrentDrugs([...currentDrugs, currentDrugInput.trim()]);
      setCurrentDrugInput('');
    }
  };

  const removeDrug = (drugToRemove: string) => {
    setCurrentDrugs(currentDrugs.filter(d => d !== drugToRemove));
  };

  const handleAnalyze = async () => {
    if (!newDrug.trim() || currentDrugs.length === 0) {
      setError("Please provide a new drug and at least one current drug.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await predictPolypharmacy({
        new_drug: newDrug.trim(),
        current_drugs: currentDrugs,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to analyze combination.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Polypharmacy Checker</h1>
        <p className="text-slate-400">Evaluate the safety of adding a new medication to an existing regimen.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        {/* Form Section */}
        <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm h-fit">
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">New Medication to Add</label>
              <Autocomplete
                value={newDrug}
                onChange={setNewDrug}
                fetchSuggestions={fetchSuggestions}
                placeholder="Search drug (e.g. aspirin)..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Current Regimen</label>
              <div className="flex space-x-2">
                <div className="flex-1">
                  <Autocomplete
                    value={currentDrugInput}
                    onChange={setCurrentDrugInput}
                    fetchSuggestions={fetchSuggestions}
                    placeholder="Search current drug..."
                    onSelect={handleAddCurrentDrug}
                  />
                </div>
                <button
                  onClick={handleAddCurrentDrug}
                  className="bg-slate-800 hover:bg-slate-700 text-white px-3 rounded-lg transition-colors border border-slate-700 flex items-center justify-center shrink-0"
                >
                  <Plus className="h-5 w-5" />
                </button>
              </div>
              
              {currentDrugs.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-4">
                  {currentDrugs.map(drug => (
                    <span key={drug} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-slate-800 border border-slate-700 text-slate-200">
                      {drug}
                      <button onClick={() => removeDrug(drug)} className="ml-2 hover:text-rose-400 focus:outline-none">
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={handleAnalyze}
              disabled={loading || !newDrug || currentDrugs.length === 0}
              className="w-full bg-cyan-500 hover:bg-cyan-400 disabled:bg-slate-800 disabled:text-slate-500 text-slate-950 font-semibold py-3 px-4 rounded-lg transition-colors flex items-center justify-center"
            >
              {loading ? (
                <><Loader2 className="animate-spin h-5 w-5 mr-2" /> Analyzing...</>
              ) : "Analyze Combination"}
            </button>
            
            {error && (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start">
                <AlertTriangle className="h-5 w-5 mr-2 shrink-0" />
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Results Section */}
        <div>
          <AnimatePresence mode="wait">
            {result ? (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="space-y-4"
              >
                <div className={`p-6 rounded-2xl border backdrop-blur-sm shadow-xl ${
                  result.overall_verdict === 'SAFE' ? 'bg-emerald-500/10 border-emerald-500/30' :
                  result.overall_verdict === 'AVOID' ? 'bg-rose-500/10 border-rose-500/30' :
                  'bg-yellow-500/10 border-yellow-500/30'
                }`}>
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-bold text-white">Overall Safety Verdict</h2>
                    {result.overall_verdict === 'SAFE' && <CheckCircle className="h-8 w-8 text-emerald-400" />}
                    {result.overall_verdict === 'AVOID' && <AlertTriangle className="h-8 w-8 text-rose-400" />}
                    {result.overall_verdict === 'CAUTION' && <Info className="h-8 w-8 text-yellow-400" />}
                  </div>
                  
                  <div className="mb-2 flex items-baseline">
                    <span className={`text-4xl font-black tracking-tight ${
                      result.overall_verdict === 'SAFE' ? 'text-emerald-400' :
                      result.overall_verdict === 'AVOID' ? 'text-rose-400' :
                      'text-yellow-400'
                    }`}>
                      {result.overall_verdict}
                    </span>
                    <span className="text-slate-400 ml-3 text-lg">Score: {result.overall_score.toFixed(1)}/100</span>
                  </div>

                  {/* Progress Bar */}
                  <div className="h-2 w-full bg-slate-800/80 rounded-full overflow-hidden mt-6">
                    <motion.div 
                      initial={{ width: 0 }} animate={{ width: `${result.overall_score}%` }} transition={{ duration: 1, ease: 'easeOut' }}
                      className={`h-full ${
                        result.overall_verdict === 'SAFE' ? 'bg-emerald-400' :
                        result.overall_verdict === 'AVOID' ? 'bg-rose-400' :
                        'bg-yellow-400'
                      }`}
                    />
                  </div>
                </div>

                <h3 className="text-lg font-medium text-slate-300 mt-6 mb-2">Interaction Breakdown</h3>
                <div className="space-y-4">
                  {result.pairs.map((pair, idx) => (
                    <div key={idx} className="bg-slate-900/60 border border-slate-800 rounded-xl p-5 hover:border-slate-700 transition-colors">
                      <div className="flex justify-between items-start mb-3 border-b border-slate-800/50 pb-3">
                        <span className="font-semibold text-white text-lg capitalize">{pair.pair}</span>
                        {pair.risk_tier && (
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            pair.risk_tier === 'SAFE' ? 'bg-emerald-500/20 text-emerald-400' :
                            pair.risk_tier === 'AVOID' ? 'bg-rose-500/20 text-rose-400' :
                            'bg-yellow-500/20 text-yellow-400'
                          }`}>
                            {pair.risk_tier} ({pair.safety_score?.toFixed(0)})
                          </span>
                        )}
                      </div>
                      
                      {pair.error ? (
                        <p className="text-rose-400 text-sm mt-2">{pair.error}</p>
                      ) : (
                        <>
                          {pair.side_effects && pair.side_effects.length > 0 && (
                            <div className="mt-3">
                              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block mb-2">Predicted Complications:</span>
                              <div className="flex flex-wrap gap-2">
                                {pair.side_effects.slice(0, 5).map((se, i) => (
                                  <span key={i} className={`text-xs px-2.5 py-1.5 rounded-md inline-flex flex-col items-start ${
                                    se.severity >= 4 ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' : 
                                    se.severity === 3 ? 'bg-yellow-500/10 text-yellow-300 border border-yellow-500/20' : 
                                    'bg-slate-800 text-slate-300 border border-slate-700'
                                  }`}>
                                    <span className="font-medium capitalize">{se.effect}</span>
                                    <span className="opacity-70 mt-0.5">{se.probability.toFixed(1)}% prob.</span>
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          {pair.ai_explanation && (
  <div className="mt-5 p-6 rounded-xl bg-gradient-to-br from-slate-900 to-slate-950 border border-cyan-500/20 shadow-lg hover:shadow-cyan-500/10 transition-all duration-300">

    {/* Header */}
    <div className="flex items-center gap-2 mb-4">
      <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></div>
      <span className="text-cyan-400 font-semibold tracking-wide text-sm uppercase">
        AI Insight
      </span>
    </div>

    {/* Content */}
    <div className="space-y-4">
      {pair.ai_explanation.split("\n\n").map((para, index) => (
        <p
          key={index}
          className="text-slate-300/90 text-[15px] leading-7 tracking-wide
                     first-letter:text-lg first-letter:font-semibold first-letter:text-cyan-300
                     hover:text-slate-200 transition-colors duration-200"
        >
          {para}
        </p>
      ))}
    </div>

  </div>
)}
                        </>
                      )}
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <div key="placeholder" className="h-full border border-slate-800/50 border-dashed rounded-2xl flex items-center justify-center p-12 text-center bg-slate-900/10">
                <p className="text-slate-500">Add medications and run the analysis to view intelligent safety profiles and interaction warnings here.</p>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

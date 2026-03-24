import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Minus, X, AlertTriangle, CheckCircle, Info, Loader2, ChevronDown } from 'lucide-react';
import { predictPolypharmacy, searchDrugs } from '../api';
import type { PredictResponse, PredictionPair } from '../types';
import Autocomplete from '../components/Autocomplete';

const InteractionCard = ({ pair }: { pair: PredictionPair }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden hover:border-slate-700 transition-colors">
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex justify-between items-start p-5 cursor-pointer bg-slate-900/40 hover:bg-slate-800/40 transition-colors"
      >
        <div className="flex flex-col gap-3 pr-4">
          <span className="font-semibold text-white text-lg capitalize">{pair.pair}</span>
          
          {pair.side_effects && pair.side_effects.length > 0 && (
            <div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider block mb-2">Predicted Complications:</span>
              <div className="flex flex-wrap gap-2">
                {pair.side_effects.slice(0, 5).map((se, i) => (
                  <span key={i} className={`text-xs px-2.5 py-1.5 rounded-md inline-flex flex-col items-start ${
                    se.severity >= 4 ? 'bg-rose-500/10 text-rose-300 border border-rose-500/20' : 
                    se.severity === 3 ? 'bg-yellow-500/10 text-yellow-300 border border-yellow-500/20' : 
                    'bg-slate-800 text-slate-300 border border-slate-700'
                  }`}>
                    <span className="font-medium capitalize">{se.effect}</span>
                    <span className="opacity-70 mt-0.5">{se.probability.toFixed(1)}%</span>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4 pl-2 mt-0.5">
          {pair.risk_tier && (
            <span className={`px-3 py-1.5 rounded-lg text-xs font-bold whitespace-nowrap ${
              pair.risk_tier === 'SAFE' ? 'bg-emerald-500/20 text-emerald-400' :
              pair.risk_tier === 'AVOID' ? 'bg-rose-500/20 text-rose-400' :
              'bg-yellow-500/20 text-yellow-400'
            }`}>
              {pair.risk_tier} ({pair.safety_score?.toFixed(0)})
            </span>
          )}
          <ChevronDown className={`w-5 h-5 text-slate-500 transition-transform shrink-0 ${isOpen ? 'rotate-180 text-cyan-500' : ''}`} />
        </div>
      </div>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t border-slate-800/50"
          >
            <div className={`p-5 bg-slate-900/60 ${pair.error || !pair.ai_explanation ? 'pt-4' : 'pt-5'}`}>
              {pair.error ? (
                <p className="text-rose-400 text-sm">{pair.error}</p>
              ) : (
                pair.ai_explanation ? (
                  <div className="p-4 bg-slate-950/80 rounded-lg text-sm text-slate-300 border-l-2 border-cyan-500 shadow-inner leading-relaxed space-y-4">
                    <div>
                      <span className="font-semibold text-cyan-400 block mb-1">What is it?</span>
                      <p>{pair.ai_explanation.what_is_it}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-emerald-400 block mb-1">What did we find?</span>
                      <p>{pair.ai_explanation.what_did_we_find}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-yellow-400 block mb-1">Side effects to watch for:</span>
                      <p>{pair.ai_explanation.side_effects_to_watch}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-emerald-400 block mb-1">Safe usage tips:</span>
                      <p>{pair.ai_explanation.safe_usage_tips}</p>
                    </div>
                    <div>
                      <span className="font-semibold text-rose-400 block mb-1">When to call your doctor:</span>
                      <p>{pair.ai_explanation.when_to_call_doctor}</p>
                    </div>
                  </div>
                ) : (
                   <p className="text-slate-500 text-sm italic">No AI explanation available.</p>
                )
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default function PolypharmacyPredictor() {
  const [newDrug, setNewDrug] = useState('');
  const [currentDrugs, setCurrentDrugs] = useState<string[]>([]);
  const [currentDrugInput, setCurrentDrugInput] = useState('');
  
  const [age, setAge] = useState<number | ''>('');
  const [gender, setGender] = useState<string>('');
  const [genderOpen, setGenderOpen] = useState(false);
  const genderRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (genderRef.current && !genderRef.current.contains(e.target as Node)) {
        setGenderOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
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

  const handleAddCurrentDrug = (selectedVal?: any) => {
    const valToAdd = (typeof selectedVal === 'string' ? selectedVal : currentDrugInput).trim();
    if (valToAdd && !currentDrugs.includes(valToAdd)) {
      setCurrentDrugs([...currentDrugs, valToAdd]);
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
        age: age === '' ? undefined : age,
        gender: gender || undefined,
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

            <div className="flex gap-4">
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-300 mb-2">Age</label>
                <div className="relative flex items-center w-full bg-slate-950 border border-slate-800 rounded-lg focus-within:border-cyan-500 focus-within:ring-1 focus-within:ring-cyan-500 transition-colors">
                  <button 
                    onClick={() => setAge(prev => (typeof prev === 'number' && prev > 0) ? prev - 1 : (prev === '' ? 39 : prev))}
                    className="p-3 text-slate-500 hover:text-cyan-400 transition-colors rounded-l-lg hover:bg-slate-900"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <input
                    type="number"
                    min="0"
                    max="120"
                    value={age}
                    onChange={(e) => setAge(e.target.value ? Number(e.target.value) : '')}
                    className="flex-1 bg-transparent text-center text-white placeholder-slate-500 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none font-medium"
                  />
                  <button 
                    onClick={() => setAge(prev => (typeof prev === 'number' ? prev + 1 : 1))}
                    className="p-3 text-slate-500 hover:text-cyan-400 transition-colors rounded-r-lg hover:bg-slate-900"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-slate-300 mb-2">Gender</label>
                <div className="relative w-full" ref={genderRef}>
                  <div
                    onClick={() => setGenderOpen(!genderOpen)}
                    className={`w-full bg-slate-950 border ${genderOpen ? 'border-cyan-500 ring-1 ring-cyan-500' : 'border-slate-800'} rounded-lg py-3 pl-4 pr-10 text-white focus:outline-none transition-colors cursor-pointer flex items-center justify-between font-medium`}
                  >
                    <span className={gender ? "capitalize" : "text-slate-500 font-normal"}>{gender || "Select gender..."}</span>
                    <ChevronDown className={`absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500 transition-transform pointer-events-none ${genderOpen ? 'rotate-180 text-cyan-500' : ''}`} />
                  </div>
                  
                  <AnimatePresence>
                    {genderOpen && (
                      <motion.ul
                        initial={{ opacity: 0, y: -5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -5 }}
                        transition={{ duration: 0.15 }}
                        className="absolute z-50 w-full mt-2 bg-slate-900 border border-slate-800 rounded-lg shadow-xl overflow-hidden"
                      >
                        {['male', 'female', 'other'].map((opt) => (
                          <li
                            key={opt}
                            onClick={() => {
                              setGender(opt);
                              setGenderOpen(false);
                            }}
                            className={`px-4 py-3 hover:bg-slate-800 cursor-pointer transition-colors border-b border-slate-800/50 last:border-0 capitalize ${gender === opt ? 'text-cyan-400 font-medium bg-slate-800/50' : 'text-slate-200'}`}
                          >
                            {opt}
                          </li>
                        ))}
                      </motion.ul>
                    )}
                  </AnimatePresence>
                </div>
              </div>
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
                    <InteractionCard key={idx} pair={pair} />
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

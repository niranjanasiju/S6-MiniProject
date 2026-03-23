import { useState, useEffect, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface AutocompleteProps {
  value: string;
  onChange: (val: string) => void;
  fetchSuggestions: (query: string) => Promise<string[]>;
  placeholder?: string;
  className?: string;
  onSelect?: () => void;
}

export default function Autocomplete({
  value,
  onChange,
  fetchSuggestions,
  placeholder = 'Search...',
  className = '',
  onSelect
}: AutocompleteProps) {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (!value.trim() || !open) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await fetchSuggestions(value);
        setSuggestions(results);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [value, open, fetchSuggestions]);

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500" />
        <input
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
          }}
          onFocus={() => {
            if (value.trim()) setOpen(true);
          }}
          placeholder={placeholder}
          className={`w-full bg-slate-950 border border-slate-800 rounded-lg py-3 pl-10 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-colors ${className}`}
        />
        {loading && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-500 animate-spin" />
        )}
      </div>

      {open && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-slate-900 border border-slate-800 rounded-lg shadow-xl max-h-60 overflow-y-auto">
          {suggestions.map((s, idx) => (
            <li
              key={idx}
              className="px-4 py-3 hover:bg-slate-800 cursor-pointer text-slate-200 transition-colors border-b border-slate-800/50 last:border-0"
              onClick={() => {
                onChange(s);
                setOpen(false);
                if (onSelect) onSelect();
              }}
            >
              {s}
            </li>
          ))}
        </ul>
      )}
      
      {open && !loading && value.trim() && suggestions.length === 0 && (
        <div className="absolute z-50 w-full mt-1 bg-slate-900 border border-slate-800 rounded-lg shadow-xl px-4 py-3 text-slate-500">
          No matches found.
        </div>
      )}
    </div>
  );
}

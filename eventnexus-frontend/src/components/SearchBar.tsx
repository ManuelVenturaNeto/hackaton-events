import { Search, MapPin, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';

interface SearchBarProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
}

export function SearchBar({ query, setQuery, onSearch }: SearchBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="w-full max-w-3xl mx-auto"
    >
      <div className="bg-white/95 backdrop-blur-xl rounded-[56px] shadow-[0_8px_32px_rgba(0,0,0,0.12)] p-1.5 flex flex-col md:flex-row items-center gap-1 border border-white/80 ring-1 ring-black/[0.03]">
        <div className="flex-1 flex items-center px-5 w-full">
          <Search className="w-5 h-5 text-brand-bright/60 mr-3 shrink-0" />
          <input
            type="text"
            placeholder="Buscar eventos, empresas ou organizadores..."
            className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/40 text-[15px]"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
          />
        </div>

        <div className="hidden md:block w-px h-7 bg-border-gray/60" />

        <div className="hidden md:flex items-center px-4 w-56">
          <MapPin className="w-4 h-4 text-brand-bright/60 mr-2.5 shrink-0" />
          <input
            type="text"
            placeholder="Localização"
            className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/40 text-[15px]"
          />
        </div>

        <button
          onClick={onSearch}
          className="btn-pill btn-primary w-full md:w-auto px-7 py-2.5 text-[14px] shadow-md shadow-brand-cta/25"
        >
          <Sparkles className="w-4 h-4" />
          Buscar
        </button>
      </div>
    </motion.div>
  );
}

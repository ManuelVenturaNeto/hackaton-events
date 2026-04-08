import { Search, MapPin } from 'lucide-react';

interface SearchBarProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
}

export function SearchBar({ query, setQuery, onSearch }: SearchBarProps) {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-[56px] shadow-lg p-2 flex flex-col md:flex-row items-center gap-2 border border-border-gray">
        <div className="flex-1 flex items-center px-4 w-full">
          <Search className="w-5 h-5 text-brand-bright mr-3" />
          <input
            type="text"
            placeholder="Buscar eventos, empresas ou organizadores..."
            className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/50"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onSearch()}
          />
        </div>

        <div className="hidden md:block w-px h-8 bg-border-gray" />

        <div className="hidden md:flex items-center px-4 w-64">
          <MapPin className="w-5 h-5 text-brand-bright mr-3" />
          <input
            type="text"
            placeholder="Localização"
            className="w-full py-3 outline-none text-brand-navy placeholder:text-text-body/50"
          />
        </div>

        <button
          onClick={onSearch}
          className="btn-pill btn-primary w-full md:w-auto px-8"
        >
          Buscar
        </button>
      </div>
    </div>
  );
}

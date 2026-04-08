import { Search, MapPin, Sparkles } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { motion } from 'motion/react';
import { Event, LocationSuggestion } from '../types';
import { AutocompleteInput } from './AutocompleteInput';

interface SearchBarProps {
  query: string;
  setQuery: (q: string) => void;
  onSearch: () => void;
  locationQuery: string;
  setLocationQuery: (q: string) => void;
  eventSuggestions: Event[];
  locationSuggestions: LocationSuggestion[];
  onSelectEvent: (event: Event) => void;
  onSelectLocation: (location: LocationSuggestion) => void;
}

export function SearchBar({
  query,
  setQuery,
  onSearch,
  locationQuery,
  setLocationQuery,
  eventSuggestions,
  locationSuggestions,
  onSelectEvent,
  onSelectLocation,
}: SearchBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="w-full max-w-3xl mx-auto"
    >
      <div className="bg-white/95 backdrop-blur-xl rounded-[56px] shadow-[0_8px_32px_rgba(0,0,0,0.12)] p-1.5 flex flex-col md:flex-row items-center gap-1 border border-white/80 ring-1 ring-black/[0.03]">

        {/* Event search autocomplete */}
        <div className="flex-1 flex items-center px-5 w-full">
          <AutocompleteInput<Event>
            value={query}
            onChange={setQuery}
            onSelect={onSelectEvent}
            suggestions={eventSuggestions}
            getItemValue={e => e.name}
            minChars={2}
            maxSuggestions={6}
            placeholder="Buscar eventos, empresas ou organizadores..."
            icon={<Search className="w-5 h-5 text-brand-bright/60 shrink-0" />}
            renderSuggestion={(event, isActive) => (
              <div className={`px-4 py-3 cursor-pointer ${isActive ? 'bg-bg-light' : 'hover:bg-bg-light'}`}>
                <p className="font-semibold text-brand-navy text-sm">{event.name}</p>
                <p className="text-xs text-text-body mt-0.5">
                  {event.location.city}, {event.location.country}
                  {event.startDate ? ` · ${format(new Date(event.startDate), "d 'de' MMM. 'de' yyyy", { locale: ptBR })}` : ''}
                </p>
              </div>
            )}
          />
        </div>

        <div className="hidden md:block w-px h-7 bg-border-gray/60" />

        {/* Location autocomplete */}
        <div className="hidden md:flex items-center px-4 w-56">
          <AutocompleteInput<LocationSuggestion>
            value={locationQuery}
            onChange={setLocationQuery}
            onSelect={onSelectLocation}
            suggestions={locationSuggestions}
            getItemValue={loc => loc.value}
            minChars={2}
            maxSuggestions={8}
            placeholder="Localização"
            icon={<MapPin className="w-4 h-4 text-brand-bright/60 shrink-0" />}
            renderSuggestion={(loc, isActive) => (
              <div className={`px-4 py-3 cursor-pointer flex items-center justify-between ${isActive ? 'bg-bg-light' : 'hover:bg-bg-light'}`}>
                <span className="text-sm font-medium text-brand-navy">{loc.value}</span>
                <span className="text-xs text-text-body bg-bg-light border border-border-gray px-2 py-0.5 rounded-full ml-2">
                  {loc.type}
                </span>
              </div>
            )}
          />
        </div>

        <button
          onClick={onSearch}
          className="btn-pill btn-primary w-full md:w-auto px-7 py-2.5 text-[14px] shadow-md shadow-brand-cta/25 flex items-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          Buscar
        </button>
      </div>
    </motion.div>
  );
}

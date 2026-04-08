import { Search, MapPin } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
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
    <div className="w-full max-w-4xl mx-auto">
      <div className="bg-white rounded-[56px] shadow-lg p-2 flex flex-col md:flex-row items-center gap-2 border border-border-gray">

        {/* Event search autocomplete */}
        <div className="flex-1 flex items-center px-4 w-full">
          <AutocompleteInput<Event>
            value={query}
            onChange={setQuery}
            onSelect={onSelectEvent}
            suggestions={eventSuggestions}
            getItemValue={e => e.name}
            minChars={2}
            maxSuggestions={6}
            placeholder="Buscar eventos, empresas ou organizadores..."
            icon={<Search className="w-5 h-5 text-brand-bright" />}
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

        <div className="hidden md:block w-px h-8 bg-border-gray" />

        {/* Location autocomplete */}
        <div className="hidden md:flex items-center px-4 w-64">
          <AutocompleteInput<LocationSuggestion>
            value={locationQuery}
            onChange={setLocationQuery}
            onSelect={onSelectLocation}
            suggestions={locationSuggestions}
            getItemValue={loc => loc.value}
            minChars={2}
            maxSuggestions={8}
            placeholder="Localização"
            icon={<MapPin className="w-5 h-5 text-brand-bright" />}
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
          className="btn-pill btn-primary w-full md:w-auto px-8"
        >
          Buscar
        </button>
      </div>
    </div>
  );
}

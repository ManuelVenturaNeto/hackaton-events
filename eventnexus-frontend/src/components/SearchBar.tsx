import { Search, MapPin, Sparkles, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { motion } from 'motion/react';
import { Event, LocationSuggestion } from '../types';
import { AutocompleteInput } from './AutocompleteInput';
import { countryFlag } from '../lib/flags';
import { categoryLabels, t } from '../lib/labels';

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
              <div className={`px-3 py-2.5 rounded-xl cursor-pointer transition-colors duration-100 ${isActive ? 'bg-brand-bright/5' : 'hover:bg-bg-light'}`}>
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-brand-bright/8 flex items-center justify-center shrink-0 mt-0.5">
                    <Calendar className="w-3.5 h-3.5 text-brand-bright/60" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-brand-navy text-[13px] leading-snug truncate">{event.name}</p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-lg leading-none">{countryFlag(event.location.country)}</span>
                      <span className="text-[11px] text-text-body/60">
                        {event.location.city}{event.location.country ? `, ${event.location.country}` : ''}
                      </span>
                      {event.startDate && (
                        <>
                          <span className="text-text-body/20">·</span>
                          <span className="text-[11px] text-text-body/50">
                            {format(new Date(event.startDate), "d MMM yyyy", { locale: ptBR })}
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                  <span className="text-[9px] font-bold text-brand-bright/50 uppercase tracking-wider bg-brand-bright/5 px-1.5 py-0.5 rounded shrink-0 mt-1">
                    {t(categoryLabels, event.category)}
                  </span>
                </div>
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
              <div className={`px-3 py-2.5 rounded-xl cursor-pointer transition-colors duration-100 flex items-center gap-3 ${isActive ? 'bg-brand-bright/5' : 'hover:bg-bg-light'}`}>
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-bg-light to-white border border-border-gray/40 flex items-center justify-center shrink-0 shadow-sm">
                  <span className="text-xl leading-none">{countryFlag(loc.country || loc.value)}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[13px] font-semibold text-brand-navy leading-snug truncate">{loc.value}</p>
                  {loc.filterKey === 'city' && loc.country && (
                    <p className="text-[11px] text-text-body/50 mt-0.5">{loc.country}</p>
                  )}
                </div>
                <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-1 rounded-full shrink-0 ${
                  loc.filterKey === 'city'
                    ? 'text-brand-bright/60 bg-brand-bright/5'
                    : 'text-brand-navy/40 bg-brand-navy/5'
                }`}>
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

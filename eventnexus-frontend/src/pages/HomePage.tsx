import { useState, useEffect, useMemo } from 'react';
import { Event, SearchFilters, SortOption, LocationSuggestion } from '../types';
import { fetchEvents } from '../api';
import { SearchBar } from '../components/SearchBar';
import { EventCard } from '../components/EventCard';
import { FilterSidebar } from '../components/FilterSidebar';
import { EventDetails } from '../components/EventDetails';
import { SyncButton } from '../components/SyncButton';
import { motion, AnimatePresence } from 'motion/react';
import { Filter, SlidersHorizontal, Loader2, AlertCircle, Compass, Plane } from 'lucide-react';

export function HomePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [allEvents, setAllEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [locationQuery, setLocationQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('highest-score');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

  const eventSuggestions = useMemo(() => {
    if (searchQuery.length < 2) return [] as Event[];
    const q = searchQuery.toLowerCase();
    return allEvents.filter(e => e.name.toLowerCase().includes(q));
  }, [allEvents, searchQuery]);

  const locationSuggestions = useMemo((): LocationSuggestion[] => {
    const seen = new Set<string>();
    const result: LocationSuggestion[] = [];
    for (const event of allEvents) {
      const candidates: LocationSuggestion[] = [
        { value: event.location.city, type: 'Cidade', filterKey: 'city', country: event.location.country },
        { value: event.location.country, type: 'País', filterKey: 'country', country: event.location.country },
      ];
      for (const c of candidates) {
        const key = `${c.type}:${c.value.toLowerCase()}`;
        if (c.value && !seen.has(key)) {
          seen.add(key);
          result.push(c);
        }
      }
    }
    return result;
  }, [allEvents]);

  function handleSelectEvent(event: Event) {
    setSearchQuery(event.name);
    setFilters(f => ({ ...f, search: event.name }));
  }

  function handleSelectLocation(loc: LocationSuggestion) {
    setLocationQuery(loc.value);
    setFilters(f => ({
      ...f,
      city: loc.filterKey === 'city' ? loc.value : undefined,
      country: loc.filterKey === 'country' ? loc.value : undefined,
    }));
  }

  const loadEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEvents({ ...filters, search: searchQuery || undefined });

      let sorted = [...data];
      sorted.sort((a, b) => {
        switch (sortBy) {
          case 'highest-score': return b.networkingRelevanceScore - a.networkingRelevanceScore;
          case 'soonest': return new Date(a.startDate).getTime() - new Date(b.startDate).getTime();
          case 'largest-audience': return (b.expectedAudienceSize || 0) - (a.expectedAudienceSize || 0);
          case 'most-companies': return b.companiesInvolved.length - a.companiesInvolved.length;
          case 'recently-updated': return new Date(b.lastUpdated).getTime() - new Date(a.lastUpdated).getTime();
          default: return 0;
        }
      });

      setEvents(sorted);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Ocorreu um erro');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents({}).then(data => setAllEvents(data)).catch(() => {});
  }, []);

  useEffect(() => {
    loadEvents();
  }, [filters, sortBy]);

  return (
    <>
      {/* Hero Section */}
      <header className="hero-gradient text-white relative overflow-hidden pt-16 pb-28 px-6">
        {/* Grid overlay */}
        <div className="hero-grid absolute inset-0" />

        {/* Floating orbs */}
        <div className="absolute top-16 left-[10%] w-72 h-72 bg-brand-bright/10 rounded-full blur-[100px] float-orb" />
        <div className="absolute bottom-8 right-[10%] w-96 h-96 bg-brand-primary/8 rounded-full blur-[120px] float-orb-delayed" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-cta/5 rounded-full blur-[150px]" />

        {/* Geometric accents */}
        <div className="absolute top-20 right-[15%] w-24 h-24 border border-white/[0.06] rounded-2xl rotate-12" />
        <div className="absolute bottom-24 left-[12%] w-16 h-16 border border-white/[0.04] rounded-xl -rotate-6" />

        <div className="max-w-7xl mx-auto relative z-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: 'easeOut' }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="inline-flex items-center gap-2 bg-white/[0.08] backdrop-blur-sm border border-white/[0.08] text-brand-bright px-4 py-2 rounded-full text-xs font-semibold uppercase tracking-widest mb-8"
            >
              <Plane className="w-3.5 h-3.5" />
              Mapeador de Eventos Corporativos
            </motion.div>

            <h1 className="text-6xl md:text-8xl font-extrabold mb-3 leading-none tracking-tighter">
              <span className="text-gradient">OnEvents</span>
            </h1>
            <p className="text-white/30 text-xs font-medium uppercase tracking-[0.3em] mb-8">
              powered by Onfly
            </p>
            <p className="text-white/50 text-base md:text-lg max-w-xl mx-auto mb-12 leading-relaxed font-light">
              Agregamos os eventos mais relevantes de tecnologia e negócios.
              Priorize o potencial de networking para sua viagem corporativa.
            </p>
          </motion.div>

          <SearchBar
            query={searchQuery}
            setQuery={setSearchQuery}
            onSearch={loadEvents}
            locationQuery={locationQuery}
            setLocationQuery={setLocationQuery}
            eventSuggestions={eventSuggestions}
            locationSuggestions={locationSuggestions}
            onSelectEvent={handleSelectEvent}
            onSelectLocation={handleSelectLocation}
          />

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex justify-center gap-8 mt-10"
          >
            {[
              { value: '1.500+', label: 'Eventos' },
              { value: '32', label: 'Países' },
              { value: '5', label: 'Fontes' },
            ].map((stat, i) => (
              <div key={i} className="text-center">
                <p className="text-white/90 text-3xl md:text-4xl font-extrabold">{stat.value}</p>
                <p className="text-white/40 text-xs uppercase tracking-wider font-medium mt-1">{stat.label}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-10 flex gap-8">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-64 shrink-0">
          <div className="sticky top-6 card-glass overflow-hidden">
            <FilterSidebar filters={filters} setFilters={setFilters} />
          </div>
        </aside>

        {/* Event List */}
        <div className="flex-1">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="text-xl font-bold text-brand-navy">
                {loading ? 'Buscando eventos...' : `${events.length} eventos encontrados`}
              </h2>
              <p className="text-sm text-text-body/60">
                Ordenados por relevância de networking
              </p>
            </div>

            <div className="flex items-center gap-2.5">
              <SyncButton />

              <div className="flex items-center gap-2 bg-white border border-border-gray/60 px-3.5 py-2 rounded-full text-sm font-medium text-brand-navy shadow-sm">
                <SlidersHorizontal className="w-3.5 h-3.5 text-brand-bright/60" />
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="bg-transparent outline-none cursor-pointer text-brand-cta text-[13px]"
                >
                  <option value="highest-score">Score de Networking</option>
                  <option value="soonest">Data mais próxima</option>
                  <option value="largest-audience">Público</option>
                  <option value="most-companies">Empresas</option>
                  <option value="recently-updated">Atualização recente</option>
                </select>
              </div>

              <button
                onClick={() => setShowMobileFilters(true)}
                className="lg:hidden p-2 bg-white border border-border-gray/60 rounded-full text-brand-navy shadow-sm"
              >
                <Filter className="w-4 h-4" />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 text-text-body">
              <div className="relative">
                <Loader2 className="w-10 h-10 animate-spin text-brand-cta/30" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="w-3 h-3 bg-brand-cta rounded-full animate-pulse" />
                </div>
              </div>
              <p className="font-medium mt-4 text-sm text-text-body/60">Buscando fontes confiáveis...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50/80 border border-red-100 p-8 rounded-2xl text-center">
              <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-red-900 mb-2">Ops! Algo deu errado</h3>
              <p className="text-red-600/80 mb-5 text-sm">{error}</p>
              <button onClick={loadEvents} className="btn-pill bg-red-500 text-white hover:bg-red-600 text-sm px-5 py-2">
                Tentar Novamente
              </button>
            </div>
          ) : events.length === 0 ? (
            <div className="bg-white border border-border-gray/50 p-16 rounded-2xl text-center">
              <div className="w-16 h-16 bg-brand-bright/5 rounded-2xl flex items-center justify-center mx-auto mb-5">
                <Compass className="w-7 h-7 text-brand-bright/30" />
              </div>
              <h3 className="text-lg font-bold text-brand-navy mb-2">Nenhum evento encontrado</h3>
              <p className="text-text-body/60 mb-6 max-w-sm mx-auto text-sm">
                Não encontramos eventos com esses critérios. Tente ajustar os filtros.
              </p>
              <button
                onClick={() => { setFilters({}); setSearchQuery(''); }}
                className="btn-pill btn-secondary text-sm"
              >
                Limpar Filtros
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
              <AnimatePresence mode="popLayout">
                {events.map((event, i) => (
                  <motion.div
                    key={event.id}
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(i * 0.03, 0.3) }}
                  >
                    <EventCard
                      event={event}
                      onClick={setSelectedEvent}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </main>

      {/* Event Details Modal */}
      <EventDetails
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
      />

      {/* Mobile Filters Drawer */}
      <AnimatePresence>
        {showMobileFilters && (
          <div className="fixed inset-0 z-[60] lg:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowMobileFilters(false)}
              className="absolute inset-0 bg-brand-navy/70 backdrop-blur-md"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 30, stiffness: 300 }}
              className="absolute right-0 top-0 bottom-0 w-full max-w-xs bg-white shadow-2xl"
            >
              <FilterSidebar
                filters={filters}
                setFilters={setFilters}
                onClose={() => setShowMobileFilters(false)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}

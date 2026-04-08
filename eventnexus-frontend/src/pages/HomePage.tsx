import { useState, useEffect } from 'react';
import { Event, SearchFilters, SortOption } from '../types';
import { fetchEvents } from '../api';
import { SearchBar } from '../components/SearchBar';
import { EventCard } from '../components/EventCard';
import { FilterSidebar } from '../components/FilterSidebar';
import { EventDetails } from '../components/EventDetails';
import { SyncButton } from '../components/SyncButton';
import { motion, AnimatePresence } from 'motion/react';
import { Filter, SlidersHorizontal, Loader2, AlertCircle, TrendingUp } from 'lucide-react';

export function HomePage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<SortOption>('highest-score');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [showMobileFilters, setShowMobileFilters] = useState(false);

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
    loadEvents();
  }, [filters, sortBy]);

  return (
    <>
      {/* Hero Section */}
      <header className="bg-brand-navy text-white relative overflow-hidden pt-20 pb-32 px-6">
        <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
          <div className="absolute top-10 left-10 w-64 h-64 border border-white rounded-full" />
          <div className="absolute bottom-10 right-10 w-96 h-96 border border-white rounded-full" />
        </div>

        <div className="max-w-7xl mx-auto relative z-10 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block bg-brand-bright/20 text-brand-bright px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-widest mb-6">
              Mapeador de Eventos Corporativos
            </span>
            <h1 className="text-5xl md:text-7xl font-bold mb-4 leading-tight tracking-tight">
              <span className="text-brand-bright">OnEvents</span>
            </h1>
            <p className="text-white/40 text-sm font-medium uppercase tracking-widest mb-8">
              powered by <span className="text-white/60">Onfly</span>
            </p>
            <p className="text-white/60 text-lg md:text-xl max-w-2xl mx-auto mb-12">
              Agregamos os eventos mais relevantes de tecnologia e negócios.
              Priorize o potencial de networking para sua viagem corporativa.
            </p>
          </motion.div>

          <SearchBar
            query={searchQuery}
            setQuery={setSearchQuery}
            onSearch={loadEvents}
          />
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-12 flex gap-8">
        {/* Desktop Sidebar */}
        <aside className="hidden lg:block w-72 shrink-0">
          <div className="sticky top-8 card-glass overflow-hidden max-h-[calc(100vh-4rem)]  overflow-y-auto">
            <FilterSidebar filters={filters} setFilters={setFilters} />
          </div>
        </aside>

        {/* Event List */}
        <div className="flex-1">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="text-2xl font-bold text-brand-navy">
                {loading ? 'Buscando eventos...' : `${events.length} Eventos Encontrados`}
              </h2>
              <p className="text-sm text-text-body">
                Mostrando as melhores oportunidades de networking.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <SyncButton />

              <div className="flex items-center gap-2 bg-white border border-border-gray px-4 py-2 rounded-full text-sm font-medium text-brand-navy">
                <SlidersHorizontal className="w-4 h-4 text-brand-bright" />
                <span>Ordenar:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="bg-transparent outline-none cursor-pointer text-brand-cta"
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
                className="lg:hidden p-2 bg-white border border-border-gray rounded-full text-brand-navy"
              >
                <Filter className="w-5 h-5" />
              </button>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-32 text-text-body">
              <Loader2 className="w-12 h-12 animate-spin text-brand-cta mb-4" />
              <p className="font-medium">Buscando fontes confiáveis...</p>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-100 p-8 rounded-3xl text-center">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-red-900 mb-2">Ops! Algo deu errado</h3>
              <p className="text-red-700 mb-6">{error}</p>
              <button onClick={loadEvents} className="btn-pill bg-red-600 text-white hover:bg-red-700">
                Tentar Novamente
              </button>
            </div>
          ) : events.length === 0 ? (
            <div className="bg-white border border-border-gray p-16 rounded-3xl text-center">
              <div className="w-20 h-20 bg-bg-light rounded-full flex items-center justify-center mx-auto mb-6">
                <TrendingUp className="w-10 h-10 text-brand-bright opacity-20" />
              </div>
              <h3 className="text-xl font-bold text-brand-navy mb-2">Nenhum evento encontrado</h3>
              <p className="text-text-body mb-8 max-w-md mx-auto">
                Não encontramos eventos com esses critérios. Tente ajustar os filtros ou a busca.
              </p>
              <button
                onClick={() => { setFilters({}); setSearchQuery(''); }}
                className="btn-pill btn-secondary"
              >
                Limpar Filtros
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence mode="popLayout">
                {events.map(event => (
                  <EventCard
                    key={event.id}
                    event={event}
                    onClick={setSelectedEvent}
                  />
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
              className="absolute inset-0 bg-brand-navy/60 backdrop-blur-sm"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
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

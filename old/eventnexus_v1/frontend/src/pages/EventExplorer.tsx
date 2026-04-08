import React, { useEffect, useState } from 'react';
import { Search, SlidersHorizontal, RefreshCw, ChevronLeft, ChevronRight, Check } from 'lucide-react';
import { EventCard } from '../components/EventCard';
import { useEvents } from '../hooks/useEvents';
import { GetEventsParams } from '../api/eventsApi';

const PAGE_SIZE = 20;

interface ToggleChipProps {
  label: string;
  active: boolean;
  onClick: () => void;
}

function ToggleChip({ label, active, onClick }: ToggleChipProps) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
        active
          ? 'bg-blue-600 text-white border-blue-600'
          : 'bg-white text-gray-600 border-gray-300 hover:border-gray-400 hover:bg-gray-50'
      }`}
    >
      {active && <Check className="h-3 w-3" />}
      {label}
    </button>
  );
}

const STATUS_OPTIONS = [
  { value: 'upcoming', label: 'Próximo' },
  { value: 'completed', label: 'Concluído' },
  { value: 'postponed', label: 'Adiado' },
  { value: 'canceled', label: 'Cancelado' },
];

const CATEGORY_OPTIONS = [
  { value: 'Technology', label: 'Tecnologia' },
  { value: 'Banking / Financial', label: 'Bancário / Financeiro' },
  { value: 'Agribusiness / Agriculture', label: 'Agronegócio / Agricultura' },
  { value: 'Medical / Healthcare', label: 'Médico / Saúde' },
  { value: 'Business / Entrepreneurship', label: 'Negócios / Empreendedorismo' },
];

const FORMAT_OPTIONS = [
  { value: 'in-person', label: 'Presencial' },
  { value: 'hybrid', label: 'Híbrido' },
  { value: 'online', label: 'Online' },
];

const COUNTRY_OPTIONS = [
  { value: 'Brazil', label: 'Brasil' },
  { value: 'USA', label: 'EUA' },
  { value: 'UAE', label: 'Emirados Árabes' },
  { value: 'Germany', label: 'Alemanha' },
  { value: 'Spain', label: 'Espanha' },
  { value: 'Portugal', label: 'Portugal' },
  { value: 'Canada', label: 'Canadá' },
  { value: 'China', label: 'China' },
];

function toggleSet(set: Set<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) {
    next.delete(value);
  } else {
    next.add(value);
  }
  return next;
}

export function EventExplorer() {
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('networkingRelevance');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedStatuses, setSelectedStatuses] = useState<Set<string>>(new Set(['upcoming']));
  const [selectedCategories, setSelectedCategories] = useState<Set<string>>(new Set());
  const [selectedFormats, setSelectedFormats] = useState<Set<string>>(new Set());
  const [selectedCountries, setSelectedCountries] = useState<Set<string>>(new Set());
  const [page, setPage] = useState(1);

  const { events, loading, error, syncing, fetchEvents, sync } = useEvents();

  const totalPages = Math.max(1, Math.ceil(events.length / PAGE_SIZE));
  const paginatedEvents = events.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [search, sort, sortOrder, selectedStatuses, selectedCategories, selectedFormats, selectedCountries]);

  useEffect(() => {
    const debounce = setTimeout(() => {
      const params: GetEventsParams = {
        search,
        status: [...selectedStatuses].join(','),
        category: [...selectedCategories].join(','),
        format: [...selectedFormats].join(','),
        country: [...selectedCountries].join(','),
        sortBy: sort as GetEventsParams['sortBy'],
        sortOrder,
      };
      fetchEvents(params);
    }, 300);
    return () => clearTimeout(debounce);
  }, [search, sort, sortOrder, selectedStatuses, selectedCategories, selectedFormats, selectedCountries, fetchEvents]);

  const handleSync = () => {
    const params: GetEventsParams = {
      search,
      status: [...selectedStatuses].join(','),
      category: [...selectedCategories].join(','),
      format: [...selectedFormats].join(','),
      country: [...selectedCountries].join(','),
      sortBy: sort as GetEventsParams['sortBy'],
      sortOrder,
    };
    sync(params);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NetworkX</h1>
              <p className="text-sm text-gray-500">Descubra eventos de networking de alto valor</p>
            </div>

            <div className="flex-1 max-w-2xl flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar eventos, organizadores ou palavras-chave..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
              </div>
              <button
                onClick={handleSync}
                disabled={syncing}
                className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                title="Sincronizar eventos"
              >
                <RefreshCw className={`h-5 w-5 ${syncing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col md:flex-row gap-8">
        {/* Sidebar Filters */}
        <aside className="w-full md:w-64 flex-shrink-0 space-y-6">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-4 border-b border-gray-100">
              <SlidersHorizontal className="h-5 w-5 text-gray-700" />
              <h2 className="font-semibold text-gray-900">Filtros</h2>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ordenar por</label>
                <select
                  className="w-full border border-gray-300 rounded-md py-1.5 px-3 text-sm focus:ring-blue-500 focus:border-blue-500"
                  value={sort}
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === 'startDate_asc') {
                      setSort('startDate');
                      setSortOrder('asc');
                    } else {
                      setSort(val);
                      setSortOrder('desc');
                    }
                  }}
                >
                  <option value="networkingRelevance">Maior Relevância de Networking</option>
                  <option value="startDate_asc">Data Mais Próxima</option>
                  <option value="audienceSize">Maior Público</option>
                  <option value="companiesCount">Mais Empresas Envolvidas</option>
                  <option value="lastUpdated">Atualizado Recentemente</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <div className="flex flex-wrap gap-2">
                  {STATUS_OPTIONS.map(opt => (
                    <ToggleChip
                      key={opt.value}
                      label={opt.label}
                      active={selectedStatuses.has(opt.value)}
                      onClick={() => setSelectedStatuses(toggleSet(selectedStatuses, opt.value))}
                    />
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Categoria</label>
                <div className="flex flex-wrap gap-2">
                  {CATEGORY_OPTIONS.map(opt => (
                    <ToggleChip
                      key={opt.value}
                      label={opt.label}
                      active={selectedCategories.has(opt.value)}
                      onClick={() => setSelectedCategories(toggleSet(selectedCategories, opt.value))}
                    />
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Formato</label>
                <div className="flex flex-wrap gap-2">
                  {FORMAT_OPTIONS.map(opt => (
                    <ToggleChip
                      key={opt.value}
                      label={opt.label}
                      active={selectedFormats.has(opt.value)}
                      onClick={() => setSelectedFormats(toggleSet(selectedFormats, opt.value))}
                    />
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">País</label>
                <div className="flex flex-wrap gap-2">
                  {COUNTRY_OPTIONS.map(opt => (
                    <ToggleChip
                      key={opt.value}
                      label={opt.label}
                      active={selectedCountries.has(opt.value)}
                      onClick={() => setSelectedCountries(toggleSet(selectedCountries, opt.value))}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* Event Grid */}
        <div className="flex-1">
          {error && !events.length ? (
            <div className="text-center py-12 bg-white rounded-xl border border-red-200">
              <h3 className="text-lg font-medium text-red-900">Erro ao carregar eventos</h3>
              <p className="mt-1 text-red-500">{error.message}</p>
            </div>
          ) : loading && !events.length ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Nenhum evento encontrado</h3>
              <p className="mt-1 text-gray-500">Tente ajustar sua busca ou filtros.</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {paginatedEvents.map(event => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-2">
                  <button
                    onClick={() => { setPage(p => Math.max(1, p - 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                    disabled={page === 1}
                    className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="h-4 w-4" /> Anterior
                  </button>

                  <div className="flex items-center gap-1">
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(p => (
                      <button
                        key={p}
                        onClick={() => { setPage(p); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                        className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                          p === page
                            ? 'bg-blue-600 text-white'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>

                  <button
                    onClick={() => { setPage(p => Math.min(totalPages, p + 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                    disabled={page === totalPages}
                    className="inline-flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    Próxima <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              )}

              <p className="mt-4 text-center text-sm text-gray-500">
                Exibindo {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, events.length)} de {events.length} eventos
              </p>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

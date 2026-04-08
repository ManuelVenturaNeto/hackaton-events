import { SearchFilters, EventCategory, EventFormat } from '../types';
import { Filter } from 'lucide-react';
import { cn } from '../lib/utils';
import { categoryLabels, formatLabels, t } from '../lib/labels';

interface FilterSidebarProps {
  filters: SearchFilters;
  setFilters: (filters: SearchFilters) => void;
  onClose?: () => void;
}

const categories: EventCategory[] = [
  'Technology',
  'Banking / Financial',
  'Agribusiness / Agriculture',
  'Medical / Healthcare',
  'Business / Entrepreneurship',
];

const formats: EventFormat[] = ['in-person', 'hybrid', 'online'];

const dateRangeOptions = [
  { label: 'Próximos 7 dias', value: '7' },
  { label: 'Próximos 30 dias', value: '30' },
  { label: 'Próximos 90 dias', value: '90' },
  { label: 'Próximos 6 meses', value: '180' },
  { label: 'Próximo ano', value: '365' },
];

export function FilterSidebar({ filters, setFilters, onClose }: FilterSidebarProps) {
  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters({ ...filters, [key]: value === filters[key] ? undefined : value });
  };

  const clearFilters = () => {
    setFilters({});
  };

  return (
    <div className="w-full bg-white flex flex-col">
      <div className="p-6 border-b border-border-gray flex justify-between items-center">
        <div className="flex items-center gap-2 font-bold text-brand-navy">
          <Filter className="w-5 h-5" />
          <span>Filtros</span>
        </div>
        <button onClick={clearFilters} className="text-xs text-brand-bright hover:underline font-medium">
          Limpar Tudo
        </button>
      </div>

      <div className="p-6 space-y-8">
        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Categoria</h4>
          <div className="space-y-2">
            {categories.map(cat => (
              <label key={cat} className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={filters.category === cat}
                  onChange={() => updateFilter('category', cat)}
                  className="w-4 h-4 rounded border-border-gray text-brand-cta focus:ring-brand-cta"
                />
                <span className={cn(
                  'text-sm transition-colors',
                  filters.category === cat ? 'text-brand-cta font-semibold' : 'text-text-body group-hover:text-brand-navy'
                )}>
                  {t(categoryLabels, cat)}
                </span>
              </label>
            ))}
          </div>
        </section>

        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Formato</h4>
          <div className="flex flex-wrap gap-2">
            {formats.map(format => (
              <button
                key={format}
                onClick={() => updateFilter('format', format)}
                className={cn(
                  'px-3 py-1.5 rounded-full text-xs font-medium transition-all',
                  filters.format === format
                    ? 'bg-brand-cta text-white'
                    : 'bg-bg-light text-text-body hover:bg-border-gray'
                )}
              >
                {t(formatLabels, format)}
              </button>
            ))}
          </div>
        </section>

        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Data</h4>
          <div className="space-y-2">
            {dateRangeOptions.map(opt => (
              <label key={opt.value} className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="radio"
                  name="dateRange"
                  checked={filters.dateRange === opt.value}
                  onChange={() => updateFilter('dateRange', opt.value)}
                  className="w-4 h-4 border-border-gray text-brand-cta focus:ring-brand-cta"
                />
                <span className={cn(
                  'text-sm transition-colors',
                  filters.dateRange === opt.value ? 'text-brand-cta font-semibold' : 'text-text-body group-hover:text-brand-navy'
                )}>
                  {opt.label}
                </span>
              </label>
            ))}
          </div>
        </section>
      </div>

      {onClose && (
        <div className="p-6 border-t border-border-gray md:hidden">
          <button onClick={onClose} className="btn-pill btn-primary w-full">
            Ver Resultados
          </button>
        </div>
      )}
    </div>
  );
}

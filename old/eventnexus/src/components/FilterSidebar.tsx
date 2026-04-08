import { SearchFilters, EventCategory, EventFormat, EventStatus } from "../types";
import { Filter, X, ChevronDown } from "lucide-react";
import { cn } from "../lib/utils";

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
  'Business / Entrepreneurship'
];

const formats: EventFormat[] = ['in-person', 'hybrid', 'online'];
const statuses: EventStatus[] = ['upcoming', 'canceled', 'postponed', 'completed'];

export function FilterSidebar({ filters, setFilters, onClose }: FilterSidebarProps) {
  const updateFilter = (key: keyof SearchFilters, value: any) => {
    setFilters({ ...filters, [key]: value === filters[key] ? undefined : value });
  };

  const clearFilters = () => {
    setFilters({});
  };

  return (
    <div className="w-full h-full bg-white flex flex-col">
      <div className="p-6 border-b border-border-gray flex justify-between items-center">
        <div className="flex items-center gap-2 font-bold text-brand-navy">
          <Filter className="w-5 h-5" />
          <span>Filters</span>
        </div>
        <button onClick={clearFilters} className="text-xs text-brand-bright hover:underline font-medium">
          Clear All
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Category */}
        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Category</h4>
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
                  "text-sm transition-colors",
                  filters.category === cat ? "text-brand-cta font-semibold" : "text-text-body group-hover:text-brand-navy"
                )}>
                  {cat}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Format */}
        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Format</h4>
          <div className="flex flex-wrap gap-2">
            {formats.map(format => (
              <button
                key={format}
                onClick={() => updateFilter('format', format)}
                className={cn(
                  "px-3 py-1.5 rounded-full text-xs font-medium transition-all",
                  filters.format === format
                    ? "bg-brand-cta text-white"
                    : "bg-bg-light text-text-body hover:bg-border-gray"
                )}
              >
                {format}
              </button>
            ))}
          </div>
        </section>

        {/* Status */}
        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Status</h4>
          <div className="space-y-2">
            {statuses.map(status => (
              <label key={status} className="flex items-center gap-3 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={filters.status === status}
                  onChange={() => updateFilter('status', status)}
                  className="w-4 h-4 rounded border-border-gray text-brand-cta focus:ring-brand-cta"
                />
                <span className={cn(
                  "text-sm capitalize transition-colors",
                  filters.status === status ? "text-brand-cta font-semibold" : "text-text-body group-hover:text-brand-navy"
                )}>
                  {status}
                </span>
              </label>
            ))}
          </div>
        </section>

        {/* Audience Size */}
        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Min. Audience</h4>
          <select
            value={filters.minAudience || ''}
            onChange={(e) => updateFilter('minAudience', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full p-2 rounded-lg border border-border-gray text-sm focus:ring-brand-cta focus:border-brand-cta"
          >
            <option value="">Any Size</option>
            <option value="1000">1,000+</option>
            <option value="5000">5,000+</option>
            <option value="10000">10,000+</option>
            <option value="50000">50,000+</option>
          </select>
        </section>
      </div>

      {onClose && (
        <div className="p-6 border-t border-border-gray md:hidden">
          <button onClick={onClose} className="btn-pill btn-primary w-full">
            Show Results
          </button>
        </div>
      )}
    </div>
  );
}

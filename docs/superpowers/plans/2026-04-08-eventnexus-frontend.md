# EventNexus Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the EventNexus frontend as a standalone React SPA that consumes the EventNexus API, applying the Onfly visual identity and adding new pages for the corporate travel use case.

**Architecture:** React 19 + Vite + Tailwind CSS 4 SPA. No backend server — the frontend is a static build served separately, calling the FastAPI API at a configurable base URL. Client-side routing via simple state (no router library needed for the 3 views). Components are split by responsibility: layout, pages, shared UI.

**Tech Stack:** React 19, Vite 6, TypeScript, Tailwind CSS 4, Motion (framer-motion), Lucide React icons, date-fns, clsx + tailwind-merge.

**IMPORTANT RULE:** Each task ends with a git commit to main and push to remote describing what was completed. All commits MUST be tagged with `frontend` (create the tag `frontend` on the first commit if it doesn't exist, then move it forward on each subsequent commit using `git tag -f frontend && git push origin frontend -f`).

**API Base URL:** Configurable via `VITE_API_URL` env var (default: `http://localhost:8000`).

**Visual Identity:** Based on Onfly brand (from `src/visual-identity-report.md`): Poppins font, blue palette (#192a3d navy, #0c93f5 CTA, #009efb bright, #2872fa primary), pill buttons (56px radius), glassmorphic cards.

---

## Key Differences from Old Frontend

1. **Types aligned to new API contract** — field names match the EventResponse exactly (`expectedAudienceSize`, `officialWebsiteUrl`, `briefDescription`, `networkingRelevanceScore`, `companiesInvolved`, `durationDays`, `sources`)
2. **API calls go to external URL** — no `/api/events` relative path; uses `VITE_API_URL` + `/api/events`
3. **No Express server** — pure static SPA (Vite dev server for development)
4. **No Google Gemini dependency** — removed
5. **New "Sync" admin trigger** — button to call `POST /api/events/sync`
6. **Texts in Portuguese** — Brazilian market focus

---

## File Structure

```
/home/robson/code/hackaton/eventnexus-frontend/
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component with view routing
│   ├── types.ts                    # TypeScript types matching API contract
│   ├── api.ts                      # API client (fetch wrapper)
│   ├── index.css                   # Tailwind + Onfly brand theme
│   ├── lib/
│   │   └── utils.ts                # cn() utility
│   ├── components/
│   │   ├── SearchBar.tsx           # Hero search bar
│   │   ├── FilterSidebar.tsx       # Left sidebar filters
│   │   ├── EventCard.tsx           # Event card in grid
│   │   ├── EventDetails.tsx        # Event detail modal
│   │   ├── SyncButton.tsx          # Admin sync trigger
│   │   └── Header.tsx              # Shared header/nav
│   └── pages/
│       ├── HomePage.tsx            # Hero + event grid (main page)
│       └── EventPage.tsx           # Single event detail page
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── .env.example
└── .gitignore
```

---

### Task 1: Project Scaffold

**Files:**
- Create: `eventnexus-frontend/package.json`
- Create: `eventnexus-frontend/tsconfig.json`
- Create: `eventnexus-frontend/vite.config.ts`
- Create: `eventnexus-frontend/index.html`
- Create: `eventnexus-frontend/.env.example`
- Create: `eventnexus-frontend/.gitignore`

- [ ] **Step 1: Create project directory**

```bash
mkdir -p /home/robson/code/hackaton/eventnexus-frontend/{public,src/{components,pages,lib}}
```

- [ ] **Step 2: Create package.json**

Create `eventnexus-frontend/package.json`:
```json
{
  "name": "eventnexus-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@tailwindcss/vite": "^4.1.14",
    "@vitejs/plugin-react": "^5.0.4",
    "clsx": "^2.1.1",
    "date-fns": "^4.1.0",
    "lucide-react": "^0.546.0",
    "motion": "^12.23.24",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwind-merge": "^3.5.0",
    "vite": "^6.2.0"
  },
  "devDependencies": {
    "@types/node": "^22.14.0",
    "tailwindcss": "^4.1.14",
    "typescript": "~5.8.2"
  }
}
```

- [ ] **Step 3: Create tsconfig.json**

Create `eventnexus-frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "allowImportingTsExtensions": true,
    "noEmit": true,
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["src"]
}
```

- [ ] **Step 4: Create vite.config.ts**

Create `eventnexus-frontend/vite.config.ts`:
```typescript
import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
});
```

- [ ] **Step 5: Create index.html**

Create `eventnexus-frontend/index.html`:
```html
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>EventNexus — Mapeador de Eventos Corporativos</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Create .env.example and .gitignore**

Create `eventnexus-frontend/.env.example`:
```env
VITE_API_URL=http://localhost:8000
```

Create `eventnexus-frontend/.gitignore`:
```
node_modules/
dist/
.env
```

- [ ] **Step 7: Install dependencies**

```bash
cd /home/robson/code/hackaton/eventnexus-frontend && npm install
```

- [ ] **Step 8: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/
git commit -m "feat(frontend): scaffold React + Vite + Tailwind project"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 2: Theme, Types & API Client

**Files:**
- Create: `eventnexus-frontend/src/index.css`
- Create: `eventnexus-frontend/src/types.ts`
- Create: `eventnexus-frontend/src/api.ts`
- Create: `eventnexus-frontend/src/lib/utils.ts`
- Create: `eventnexus-frontend/src/main.tsx`

- [ ] **Step 1: Create index.css with Onfly brand theme**

Create `eventnexus-frontend/src/index.css`:
```css
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
@import "tailwindcss";

@theme {
  --font-sans: "Poppins", ui-sans-serif, system-ui, sans-serif;

  /* Onfly Brand Palette */
  --color-brand-primary: #2872fa;
  --color-brand-cta: #0c93f5;
  --color-brand-bright: #009efb;
  --color-brand-medium: #1476bc;
  --color-brand-dark: #1f6391;
  --color-brand-navy: #192a3d;
  --color-text-body: #3a4f66;
  --color-bg-light: #f2f5f7;
  --color-border-gray: #e1e8ed;
}

@layer base {
  body {
    @apply bg-bg-light text-text-body font-sans;
  }

  h1, h2, h3, h4, h5, h6 {
    @apply text-brand-navy font-semibold;
  }
}

@layer components {
  .btn-pill {
    @apply rounded-[56px] px-6 py-3 font-semibold transition-all duration-200 flex items-center justify-center gap-2;
  }

  .btn-primary {
    @apply bg-brand-cta text-white hover:bg-brand-dark;
  }

  .btn-secondary {
    @apply bg-white border border-border-gray text-brand-navy hover:bg-bg-light;
  }

  .card-glass {
    @apply bg-white border border-border-gray rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200;
  }
}
```

- [ ] **Step 2: Create types.ts aligned to API contract**

Create `eventnexus-frontend/src/types.ts`:
```typescript
export type EventStatus = 'upcoming' | 'canceled' | 'postponed' | 'completed';
export type EventFormat = 'in-person' | 'hybrid' | 'online';
export type EventCategory =
  | 'Technology'
  | 'Banking / Financial'
  | 'Agribusiness / Agriculture'
  | 'Medical / Healthcare'
  | 'Business / Entrepreneurship';

export interface EventLocation {
  venueName: string;
  fullStreetAddress: string;
  city: string;
  stateProvince: string;
  country: string;
  postalCode: string;
  continent: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Company {
  name: string;
  role: string;
}

export interface EventSource {
  sourceName: string;
  confidence: number;
}

export interface Event {
  id: string;
  name: string;
  organizer: string;
  category: string;
  format: string;
  status: string;
  expectedAudienceSize: number;
  officialWebsiteUrl: string;
  briefDescription: string;
  networkingRelevanceScore: number;
  startDate: string;
  endDate: string;
  durationDays: number;
  lastUpdated: string;
  location: EventLocation;
  companiesInvolved: Company[];
  sources: EventSource[];
}

export interface SearchFilters {
  category?: EventCategory;
  country?: string;
  city?: string;
  status?: EventStatus;
  format?: EventFormat;
  minAudience?: number;
  search?: string;
}

export type SortOption =
  | 'highest-score'
  | 'soonest'
  | 'largest-audience'
  | 'most-companies'
  | 'recently-updated';

export interface SyncResponse {
  status: string;
  runId: string;
  message: string;
}
```

- [ ] **Step 3: Create api.ts**

Create `eventnexus-frontend/src/api.ts`:
```typescript
import type { Event, SearchFilters, SyncResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchEvents(filters: SearchFilters = {}): Promise<Event[]> {
  const params = new URLSearchParams();
  if (filters.search) params.append('search', filters.search);
  if (filters.category) params.append('category', filters.category);
  if (filters.country) params.append('country', filters.country);
  if (filters.city) params.append('city', filters.city);
  if (filters.status) params.append('status', filters.status);
  if (filters.format) params.append('format', filters.format);
  if (filters.minAudience) params.append('minAudienceSize', filters.minAudience.toString());

  const response = await fetch(`${API_URL}/api/events?${params.toString()}`);
  if (!response.ok) throw new Error('Falha ao buscar eventos');
  return response.json();
}

export async function fetchEventById(id: string): Promise<Event> {
  const response = await fetch(`${API_URL}/api/events/${id}`);
  if (!response.ok) throw new Error('Evento não encontrado');
  return response.json();
}

export async function triggerSync(): Promise<SyncResponse> {
  const response = await fetch(`${API_URL}/api/events/sync`, { method: 'POST' });
  if (!response.ok) throw new Error('Falha ao iniciar sincronização');
  return response.json();
}

export async function checkHealth(): Promise<{ status: string; database: string }> {
  const response = await fetch(`${API_URL}/api/health`);
  if (!response.ok) throw new Error('API indisponível');
  return response.json();
}
```

- [ ] **Step 4: Create lib/utils.ts**

Create `eventnexus-frontend/src/lib/utils.ts`:
```typescript
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 5: Create main.tsx**

Create `eventnexus-frontend/src/main.tsx`:
```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

- [ ] **Step 6: Create placeholder App.tsx**

Create `eventnexus-frontend/src/App.tsx`:
```tsx
export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <h1 className="text-3xl font-bold text-brand-navy">EventNexus</h1>
    </div>
  );
}
```

- [ ] **Step 7: Verify dev server starts**

```bash
cd /home/robson/code/hackaton/eventnexus-frontend && npx vite --port 3000 &
sleep 3
curl -s http://localhost:3000 | head -5
kill %1
```
Expected: HTML content with `<div id="root">`.

- [ ] **Step 8: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/ eventnexus-frontend/public/
git commit -m "feat(frontend): add Onfly theme, types aligned to API, and API client"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 3: SearchBar Component

**Files:**
- Create: `eventnexus-frontend/src/components/SearchBar.tsx`

- [ ] **Step 1: Create SearchBar.tsx**

Create `eventnexus-frontend/src/components/SearchBar.tsx`:
```tsx
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
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/components/SearchBar.tsx
git commit -m "feat(frontend): add SearchBar component with Portuguese labels"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 4: FilterSidebar Component

**Files:**
- Create: `eventnexus-frontend/src/components/FilterSidebar.tsx`

- [ ] **Step 1: Create FilterSidebar.tsx**

Create `eventnexus-frontend/src/components/FilterSidebar.tsx`:
```tsx
import { SearchFilters, EventCategory, EventFormat, EventStatus } from '../types';
import { Filter } from 'lucide-react';
import { cn } from '../lib/utils';

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

const categoryLabels: Record<EventCategory, string> = {
  'Technology': 'Tecnologia',
  'Banking / Financial': 'Bancos / Financeiro',
  'Agribusiness / Agriculture': 'Agronegócio',
  'Medical / Healthcare': 'Saúde / Medicina',
  'Business / Entrepreneurship': 'Negócios / Empreendedorismo',
};

const formats: EventFormat[] = ['in-person', 'hybrid', 'online'];
const formatLabels: Record<EventFormat, string> = {
  'in-person': 'Presencial',
  'hybrid': 'Híbrido',
  'online': 'Online',
};

const statuses: EventStatus[] = ['upcoming', 'canceled', 'postponed', 'completed'];
const statusLabels: Record<EventStatus, string> = {
  'upcoming': 'Próximo',
  'canceled': 'Cancelado',
  'postponed': 'Adiado',
  'completed': 'Concluído',
};

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
          <span>Filtros</span>
        </div>
        <button onClick={clearFilters} className="text-xs text-brand-bright hover:underline font-medium">
          Limpar Tudo
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-8">
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
                  {categoryLabels[cat]}
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
                {formatLabels[format]}
              </button>
            ))}
          </div>
        </section>

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
                  'text-sm transition-colors',
                  filters.status === status ? 'text-brand-cta font-semibold' : 'text-text-body group-hover:text-brand-navy'
                )}>
                  {statusLabels[status]}
                </span>
              </label>
            ))}
          </div>
        </section>

        <section>
          <h4 className="text-sm font-bold text-brand-navy mb-4 uppercase tracking-wider">Público Mínimo</h4>
          <select
            value={filters.minAudience || ''}
            onChange={(e) => updateFilter('minAudience', e.target.value ? Number(e.target.value) : undefined)}
            className="w-full p-2 rounded-lg border border-border-gray text-sm focus:ring-brand-cta focus:border-brand-cta"
          >
            <option value="">Qualquer tamanho</option>
            <option value="1000">1.000+</option>
            <option value="5000">5.000+</option>
            <option value="10000">10.000+</option>
            <option value="50000">50.000+</option>
          </select>
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
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/components/FilterSidebar.tsx
git commit -m "feat(frontend): add FilterSidebar with Portuguese labels and Onfly brand"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 5: EventCard Component

**Files:**
- Create: `eventnexus-frontend/src/components/EventCard.tsx`

- [ ] **Step 1: Create EventCard.tsx**

Create `eventnexus-frontend/src/components/EventCard.tsx`:
```tsx
import { Event } from '../types';
import { Calendar, MapPin, Users, Building2, ExternalLink, ArrowRight, Star } from 'lucide-react';
import { motion } from 'motion/react';
import { cn } from '../lib/utils';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventCardProps {
  event: Event;
  onClick: (event: Event) => void;
}

export function EventCard({ event, onClick }: EventCardProps) {
  const isCanceled = event.status === 'canceled';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={cn(
        'card-glass overflow-hidden flex flex-col h-full group cursor-pointer',
        isCanceled && 'opacity-75 grayscale'
      )}
      onClick={() => onClick(event)}
    >
      <div className="p-5 flex-1 flex flex-col">
        <div className="flex justify-between items-start mb-3">
          <span className={cn(
            'text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full',
            event.category === 'Technology' ? 'bg-brand-bright/10 text-brand-bright' : 'bg-brand-navy/10 text-brand-navy'
          )}>
            {event.category}
          </span>
          <div className="flex gap-2">
            {event.status !== 'upcoming' && (
              <span className={cn(
                'text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full',
                isCanceled ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-600'
              )}>
                {event.status}
              </span>
            )}
            <span className="bg-green-100 text-green-700 text-[10px] font-bold uppercase tracking-wider px-2 py-1 rounded-full flex items-center gap-1">
              <Star className="w-3 h-3 fill-current" />
              {event.networkingRelevanceScore}
            </span>
          </div>
        </div>

        <h3 className="text-lg font-bold text-brand-navy mb-2 group-hover:text-brand-cta transition-colors">
          {event.name}
        </h3>

        <div className="space-y-2 mb-4 flex-1">
          <div className="flex items-center gap-2 text-sm text-text-body">
            <Calendar className="w-4 h-4 text-brand-bright" />
            <span>
              {event.startDate ? format(new Date(event.startDate), "d 'de' MMM, yyyy", { locale: ptBR }) : 'Data a definir'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm text-text-body">
            <MapPin className="w-4 h-4 text-brand-bright" />
            <span className="truncate">{event.location.city}, {event.location.country}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-text-body">
            <Building2 className="w-4 h-4 text-brand-bright" />
            <span className="truncate">{event.organizer}</span>
          </div>
          {event.expectedAudienceSize > 0 && (
            <div className="flex items-center gap-2 text-sm text-text-body">
              <Users className="w-4 h-4 text-brand-bright" />
              <span>{event.expectedAudienceSize.toLocaleString('pt-BR')}+ participantes</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-1 mb-4">
          {event.companiesInvolved.slice(0, 3).map((company, i) => (
            <span key={i} className="text-[10px] bg-bg-light px-2 py-0.5 rounded border border-border-gray">
              {company.name}
            </span>
          ))}
          {event.companiesInvolved.length > 3 && (
            <span className="text-[10px] text-brand-bright font-medium">
              +{event.companiesInvolved.length - 3} mais
            </span>
          )}
        </div>

        <div className="pt-4 border-t border-border-gray flex items-center justify-between mt-auto">
          <span className="text-xs font-medium text-brand-bright flex items-center gap-1">
            Ver Detalhes <ArrowRight className="w-3 h-3" />
          </span>
          <a
            href={event.officialWebsiteUrl}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="p-2 hover:bg-bg-light rounded-full transition-colors text-text-body hover:text-brand-cta"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </motion.div>
  );
}
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/components/EventCard.tsx
git commit -m "feat(frontend): add EventCard component with pt-BR date formatting"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 6: EventDetails Modal

**Files:**
- Create: `eventnexus-frontend/src/components/EventDetails.tsx`

- [ ] **Step 1: Create EventDetails.tsx**

Create `eventnexus-frontend/src/components/EventDetails.tsx`:
```tsx
import { Event } from '../types';
import { X, Calendar, MapPin, Users, Building2, Globe, ShieldCheck, Clock, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface EventDetailsProps {
  event: Event | null;
  onClose: () => void;
}

export function EventDetails({ event, onClose }: EventDetailsProps) {
  if (!event) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-brand-navy/60 backdrop-blur-sm"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col"
        >
          <button
            onClick={onClose}
            className="absolute top-6 right-6 p-2 hover:bg-bg-light rounded-full transition-colors z-10"
          >
            <X className="w-6 h-6 text-white" />
          </button>

          <div className="overflow-y-auto">
            {/* Header */}
            <div className="p-8 md:p-12 bg-brand-navy text-white relative overflow-hidden">
              <div className="absolute top-0 right-0 w-64 h-64 bg-brand-bright/20 rounded-full blur-3xl -mr-32 -mt-32" />
              <div className="relative z-10">
                <div className="flex flex-wrap gap-2 mb-4">
                  <span className="bg-brand-bright px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                    {event.category}
                  </span>
                  <span className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                    {event.format}
                  </span>
                  {event.status !== 'upcoming' && (
                    <span className="bg-amber-500 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest">
                      {event.status}
                    </span>
                  )}
                </div>
                <h2 className="text-3xl md:text-5xl font-bold mb-6 leading-tight text-white">
                  {event.name}
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-white/10 rounded-2xl">
                      <Calendar className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-white/60 text-xs uppercase font-bold tracking-wider">Data e Duração</p>
                      <p className="font-medium">
                        {event.startDate && format(new Date(event.startDate), "d 'de' MMMM", { locale: ptBR })}
                        {event.endDate && ` - ${format(new Date(event.endDate), "d 'de' MMMM, yyyy", { locale: ptBR })}`}
                        {event.durationDays > 0 && ` (${event.durationDays} dias)`}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-white/10 rounded-2xl">
                      <MapPin className="w-6 h-6" />
                    </div>
                    <div>
                      <p className="text-white/60 text-xs uppercase font-bold tracking-wider">Local</p>
                      <p className="font-medium">
                        {event.location.venueName || 'Local a definir'}, {event.location.city}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 md:p-12 grid grid-cols-1 lg:grid-cols-3 gap-12">
              <div className="lg:col-span-2 space-y-10">
                <section>
                  <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                    <Info className="w-5 h-5 text-brand-bright" />
                    Sobre o Evento
                  </h3>
                  <p className="text-text-body leading-relaxed text-lg">
                    {event.briefDescription || 'Descrição não disponível.'}
                  </p>
                </section>

                {event.companiesInvolved.length > 0 && (
                  <section>
                    <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                      <Building2 className="w-5 h-5 text-brand-bright" />
                      Empresas Envolvidas
                    </h3>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                      {event.companiesInvolved.map((company, i) => (
                        <div key={i} className="p-4 bg-bg-light rounded-2xl border border-border-gray">
                          <p className="font-bold text-brand-navy text-sm">{company.name}</p>
                          <p className="text-[10px] uppercase text-brand-bright font-bold tracking-wider">
                            {company.role}
                          </p>
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              <div className="space-y-6">
                <div className="p-6 bg-brand-bright/5 rounded-3xl border border-brand-bright/10">
                  <h4 className="text-brand-bright font-bold uppercase text-xs tracking-widest mb-4">
                    Potencial de Networking
                  </h4>
                  <div className="flex items-end gap-2 mb-6">
                    <span className="text-5xl font-bold text-brand-navy leading-none">
                      {event.networkingRelevanceScore}
                    </span>
                    <span className="text-brand-bright font-bold mb-1">/ 100</span>
                  </div>
                  <div className="space-y-4">
                    <div className="flex items-center gap-3 text-sm">
                      <Users className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">
                        {event.expectedAudienceSize > 0
                          ? `${event.expectedAudienceSize.toLocaleString('pt-BR')} participantes`
                          : 'Público estimado'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <ShieldCheck className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">Evento oficial verificado</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <Clock className="w-5 h-5 text-brand-bright" />
                      <span className="font-medium">
                        Atualizado em {event.lastUpdated && format(new Date(event.lastUpdated), "d 'de' MMM", { locale: ptBR })}
                      </span>
                    </div>
                  </div>
                  <a
                    href={event.officialWebsiteUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-pill btn-primary w-full mt-8"
                  >
                    Site Oficial <Globe className="w-4 h-4" />
                  </a>
                </div>

                <div className="p-6 bg-bg-light rounded-3xl border border-border-gray">
                  <h4 className="text-brand-navy font-bold uppercase text-xs tracking-widest mb-4">
                    Detalhes do Local
                  </h4>
                  <p className="text-sm font-medium text-brand-navy mb-1">{event.location.venueName}</p>
                  <p className="text-sm text-text-body mb-4">{event.location.fullStreetAddress}</p>
                  <p className="text-sm text-text-body">
                    {event.location.city}, {event.location.stateProvince}
                  </p>
                  <p className="text-sm text-text-body">{event.location.country}</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/components/EventDetails.tsx
git commit -m "feat(frontend): add EventDetails modal with networking score and pt-BR"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 7: SyncButton Component

**Files:**
- Create: `eventnexus-frontend/src/components/SyncButton.tsx`

- [ ] **Step 1: Create SyncButton.tsx**

Create `eventnexus-frontend/src/components/SyncButton.tsx`:
```tsx
import { useState } from 'react';
import { RefreshCw, Check, AlertCircle } from 'lucide-react';
import { triggerSync } from '../api';
import { cn } from '../lib/utils';

export function SyncButton() {
  const [syncing, setSyncing] = useState(false);
  const [result, setResult] = useState<'success' | 'error' | null>(null);

  const handleSync = async () => {
    setSyncing(true);
    setResult(null);
    try {
      await triggerSync();
      setResult('success');
    } catch {
      setResult('error');
    } finally {
      setSyncing(false);
      setTimeout(() => setResult(null), 3000);
    }
  };

  return (
    <button
      onClick={handleSync}
      disabled={syncing}
      className={cn(
        'btn-pill text-sm px-4 py-2 transition-all',
        result === 'success'
          ? 'bg-green-100 text-green-700 border border-green-200'
          : result === 'error'
          ? 'bg-red-100 text-red-700 border border-red-200'
          : 'btn-secondary'
      )}
    >
      {syncing ? (
        <>
          <RefreshCw className="w-4 h-4 animate-spin" />
          Sincronizando...
        </>
      ) : result === 'success' ? (
        <>
          <Check className="w-4 h-4" />
          Sincronização iniciada
        </>
      ) : result === 'error' ? (
        <>
          <AlertCircle className="w-4 h-4" />
          Erro ao sincronizar
        </>
      ) : (
        <>
          <RefreshCw className="w-4 h-4" />
          Sincronizar Eventos
        </>
      )}
    </button>
  );
}
```

- [ ] **Step 2: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/components/SyncButton.tsx
git commit -m "feat(frontend): add SyncButton component for admin sync trigger"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 8: HomePage (Main Page Assembly)

**Files:**
- Create: `eventnexus-frontend/src/pages/HomePage.tsx`
- Modify: `eventnexus-frontend/src/App.tsx`

- [ ] **Step 1: Create HomePage.tsx**

Create `eventnexus-frontend/src/pages/HomePage.tsx`:
```tsx
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

interface HomePageProps {
  onSelectEvent: (event: Event) => void;
}

export function HomePage({ onSelectEvent }: HomePageProps) {
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
            <h1 className="text-5xl md:text-7xl font-bold mb-8 leading-tight tracking-tight">
              Encontre seu próximo <br />
              <span className="text-brand-bright">evento estratégico</span>
            </h1>
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
          <div className="sticky top-8 card-glass overflow-hidden">
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
```

- [ ] **Step 2: Update App.tsx with footer and HomePage**

Replace `eventnexus-frontend/src/App.tsx` with:
```tsx
import { HomePage } from './pages/HomePage';
import { Event } from './types';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <HomePage onSelectEvent={() => {}} />

      {/* Footer */}
      <footer className="bg-white border-t border-border-gray py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-brand-cta rounded-lg flex items-center justify-center text-white font-bold">E</div>
            <span className="text-xl font-bold text-brand-navy">EventNexus</span>
          </div>
          <div className="flex gap-8 text-sm text-text-body">
            <a href="#" className="hover:text-brand-cta transition-colors">Sobre</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Fontes</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Privacidade</a>
            <a href="#" className="hover:text-brand-cta transition-colors">Termos</a>
          </div>
          <p className="text-xs text-text-body/60">
            © 2026 EventNexus. Dados agregados de fontes oficiais.
          </p>
        </div>
      </footer>
    </div>
  );
}
```

- [ ] **Step 3: Verify app compiles**

```bash
cd /home/robson/code/hackaton/eventnexus-frontend && npx vite build 2>&1 | tail -5
```
Expected: Build success with no errors.

- [ ] **Step 4: Commit and push**

```bash
cd /home/robson/code/hackaton
git add eventnexus-frontend/src/pages/HomePage.tsx eventnexus-frontend/src/App.tsx
git commit -m "feat(frontend): add HomePage with event grid, filters, sync button, and pt-BR UI"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

### Task 9: Final Verification & Polish

**Files:**
- No new files — verify everything works end-to-end.

- [ ] **Step 1: Verify build succeeds**

```bash
cd /home/robson/code/hackaton/eventnexus-frontend && npx vite build
```
Expected: `dist/` folder created with no errors.

- [ ] **Step 2: Verify dev server starts**

```bash
cd /home/robson/code/hackaton/eventnexus-frontend && npx vite --port 3000 &
sleep 3
curl -s http://localhost:3000 | grep -o "EventNexus"
kill %1
```
Expected: `EventNexus` printed.

- [ ] **Step 3: Final commit and push**

```bash
cd /home/robson/code/hackaton
git add -A
git commit -m "feat(frontend): complete EventNexus frontend v2 with Onfly brand identity"
git tag -f frontend
git push origin main && git push origin frontend -f
```

---

## Summary

| Task | Component | Key Changes from Old |
|------|-----------|---------------------|
| 1 | Scaffold | No Express server, no Gemini, standalone SPA |
| 2 | Theme + Types + API | Onfly palette, types match API contract exactly, configurable API URL |
| 3 | SearchBar | Portuguese labels |
| 4 | FilterSidebar | Portuguese labels, category/status translations |
| 5 | EventCard | `companiesInvolved`, `networkingRelevanceScore`, `expectedAudienceSize`, pt-BR dates |
| 6 | EventDetails | `briefDescription`, `durationDays`, `officialWebsiteUrl`, pt-BR |
| 7 | SyncButton | New — triggers `POST /api/events/sync` |
| 8 | HomePage | Full assembly with SyncButton, Portuguese UI |
| 9 | Verification | Build + dev server check |

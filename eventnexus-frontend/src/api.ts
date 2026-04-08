import type { Event, SearchFilters, SyncResponse } from './types';

const API_URL = import.meta.env.VITE_API_URL || '';

export async function fetchEvents(filters: SearchFilters = {}): Promise<Event[]> {
  const params = new URLSearchParams();
  if (filters.search) params.append('search', filters.search);
  if (filters.category) params.append('category', filters.category);
  if (filters.country) params.append('country', filters.country);
  if (filters.city) params.append('city', filters.city);
  if (filters.format) params.append('format', filters.format);
  if (filters.dateRange) {
    const today = new Date().toISOString().slice(0, 10);
    const end = new Date(Date.now() + Number(filters.dateRange) * 86400000).toISOString().slice(0, 10);
    params.append('startDateFrom', today);
    params.append('startDateTo', end);
  }

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

export async function fetchFlightUrl(eventId: string, origin: string = 'belo horizonte'): Promise<{ url: string | null; error: string | null }> {
  const params = new URLSearchParams({ origin });
  const response = await fetch(`${API_URL}/api/events/${eventId}/flight-url?${params}`);
  if (!response.ok) throw new Error('Falha ao gerar URL de voo');
  return response.json();
}

export async function checkHealth(): Promise<{ status: string; database: string }> {
  const response = await fetch(`${API_URL}/api/health`);
  if (!response.ok) throw new Error('API indisponível');
  return response.json();
}

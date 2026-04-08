import { Event } from '../types/event';

const API_BASE_URL = (window as any).__API_BASE_URL || 'http://localhost:8000/api';

export interface GetEventsParams {
  search?: string;
  category?: string;
  country?: string;
  city?: string;
  status?: string;
  format?: string;
  organizer?: string;
  company?: string;
  startDateFrom?: string;
  startDateTo?: string;
  endDateFrom?: string;
  endDateTo?: string;
  sortBy?: 'networkingRelevance' | 'startDate' | 'audienceSize' | 'companiesCount' | 'lastUpdated';
  sortOrder?: 'asc' | 'desc';
}

export const eventsApi = {
  async getHealth(): Promise<{ status: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  },

  async getEvents(params?: GetEventsParams): Promise<Event[]> {
    const url = new URL(`${API_BASE_URL}/events`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== '') {
          url.searchParams.append(key, value);
        }
      });
    }

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error(`Failed to fetch events: ${response.statusText}`);
    }
    return response.json();
  },

  async getEventById(eventId: string): Promise<Event> {
    const response = await fetch(`${API_BASE_URL}/events/${eventId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch event ${eventId}: ${response.statusText}`);
    }
    return response.json();
  },

  async syncEvents(): Promise<{ status: string; message?: string }> {
    const response = await fetch(`${API_BASE_URL}/events/sync`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Sync failed: ${response.statusText}`);
    }
    return response.json();
  },
};

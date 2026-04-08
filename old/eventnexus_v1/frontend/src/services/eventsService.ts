import { eventsApi, GetEventsParams } from '../api/eventsApi';
import { cache } from '../utils/cache';
import { Event } from '../types/event';
import { eventsData as mockEvents } from '../server/data';

const CACHE_KEYS = {
  EVENTS_LIST: (params: string) => `events_list_${params}`,
  EVENT_DETAIL: (id: string) => `event_detail_${id}`,
};

export const eventsService = {
  async getEvents(params: GetEventsParams = {}): Promise<Event[]> {
    const paramsString = JSON.stringify(params);
    const cacheKey = CACHE_KEYS.EVENTS_LIST(paramsString);

    // 1. Check valid cache
    const cachedData = cache.get<Event[]>(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    // 2. Fetch from API
    try {
      const data = await eventsApi.getEvents(params);
      cache.set(cacheKey, data);
      return data;
    } catch (error) {
      console.warn('API fetch failed, falling back to stale cache or mock data', error);
      
      // 3. Fallback to stale cache
      const staleData = cache.getStale<Event[]>(cacheKey);
      if (staleData) {
        return staleData;
      }

      // 4. Fallback to mock data (bootstrap)
      // We do simple filtering on mock data just to not break the UI completely
      let filtered = [...mockEvents];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(e => 
          e.name.toLowerCase().includes(q) || 
          e.organizer.toLowerCase().includes(q) ||
          e.briefDescription.toLowerCase().includes(q)
        );
      }
      if (params.category) {
        filtered = filtered.filter(e => e.category.toLowerCase() === params.category?.toLowerCase());
      }
      if (params.status) {
        filtered = filtered.filter(e => e.status.toLowerCase() === params.status?.toLowerCase());
      }
      if (params.format) {
        filtered = filtered.filter(e => e.format.toLowerCase() === params.format?.toLowerCase());
      }
      if (params.country) {
        filtered = filtered.filter(e => e.location.country.toLowerCase() === params.country?.toLowerCase());
      }
      
      return filtered as Event[];
    }
  },

  async getEventById(id: string): Promise<Event | null> {
    const cacheKey = CACHE_KEYS.EVENT_DETAIL(id);

    // 1. Check valid cache
    const cachedData = cache.get<Event>(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    // 2. Fetch from API
    try {
      const data = await eventsApi.getEventById(id);
      cache.set(cacheKey, data);
      return data;
    } catch (error) {
      console.warn(`API fetch failed for event ${id}, falling back`, error);
      
      // 3. Fallback to stale cache
      const staleData = cache.getStale<Event>(cacheKey);
      if (staleData) {
        return staleData;
      }

      // 4. Fallback to mock data
      const mockEvent = mockEvents.find(e => e.id === id);
      return (mockEvent as Event) || null;
    }
  },

  async syncEvents(): Promise<void> {
    await eventsApi.syncEvents();
  }
};

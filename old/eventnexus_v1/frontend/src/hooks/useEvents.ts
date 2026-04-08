import { useState, useEffect, useCallback } from 'react';
import { Event } from '../types/event';
import { eventsService } from '../services/eventsService';
import { GetEventsParams } from '../api/eventsApi';

export function useEvents(initialParams: GetEventsParams = {}) {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [syncing, setSyncing] = useState(false);

  const fetchEvents = useCallback(async (params: GetEventsParams) => {
    setLoading(true);
    setError(null);
    try {
      const data = await eventsService.getEvents(params);
      setEvents(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch events'));
    } finally {
      setLoading(false);
    }
  }, []);

  const sync = useCallback(async (currentParams: GetEventsParams) => {
    setSyncing(true);
    try {
      await eventsService.syncEvents();
      // Re-fetch after successful sync
      await fetchEvents(currentParams);
    } catch (err) {
      console.error('Sync failed:', err);
      // Optionally set an error state for sync specifically
    } finally {
      setSyncing(false);
    }
  }, [fetchEvents]);

  return {
    events,
    loading,
    error,
    syncing,
    fetchEvents,
    sync
  };
}

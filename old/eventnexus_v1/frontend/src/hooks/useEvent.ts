import { useState, useEffect } from 'react';
import { Event } from '../types/event';
import { eventsService } from '../services/eventsService';

export function useEvent(id: string | undefined) {
  const [event, setEvent] = useState<Event | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchEvent = async () => {
      if (!id) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const data = await eventsService.getEventById(id);
        if (mounted) {
          setEvent(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err instanceof Error ? err : new Error('Failed to fetch event'));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchEvent();

    return () => {
      mounted = false;
    };
  }, [id]);

  return {
    event,
    loading,
    error
  };
}

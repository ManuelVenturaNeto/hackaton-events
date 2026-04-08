interface CacheItem<T> {
  payload: T;
  timestamp: number;
}

const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export const cache = {
  get<T>(key: string): T | null {
    try {
      const itemStr = localStorage.getItem(key);
      if (!itemStr) return null;

      const item: CacheItem<T> = JSON.parse(itemStr);
      const now = Date.now();

      if (now - item.timestamp > CACHE_TTL_MS) {
        // Cache expired
        return null;
      }

      return item.payload;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  },

  set<T>(key: string, payload: T): void {
    try {
      const item: CacheItem<T> = {
        payload,
        timestamp: Date.now(),
      };
      localStorage.setItem(key, JSON.stringify(item));
    } catch (error) {
      console.error('Cache write error:', error);
    }
  },

  remove(key: string): void {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error('Cache remove error:', error);
    }
  },
  
  // Get stale data if needed (ignoring TTL)
  getStale<T>(key: string): T | null {
    try {
      const itemStr = localStorage.getItem(key);
      if (!itemStr) return null;
      const item: CacheItem<T> = JSON.parse(itemStr);
      return item.payload;
    } catch (error) {
      console.error('Cache read error:', error);
      return null;
    }
  }
};

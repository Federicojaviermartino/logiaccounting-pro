/**
 * Client-side caching utilities with TTL support.
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface CacheOptions {
  ttl?: number;
  staleWhileRevalidate?: boolean;
}

class ApiCache {
  private cache: Map<string, CacheEntry<any>> = new Map();
  private pendingRequests: Map<string, Promise<any>> = new Map();
  private defaultTTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Get cached data or fetch from API.
   */
  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: CacheOptions = {}
  ): Promise<T> {
    const { ttl = this.defaultTTL, staleWhileRevalidate = false } = options;

    const cached = this.cache.get(key);
    const now = Date.now();

    if (cached) {
      const isExpired = now - cached.timestamp > cached.ttl;

      if (!isExpired) {
        return cached.data as T;
      }

      if (staleWhileRevalidate) {
        this.revalidate(key, fetcher, ttl);
        return cached.data as T;
      }
    }

    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key) as Promise<T>;
    }

    const fetchPromise = fetcher().then((data) => {
      this.set(key, data, ttl);
      this.pendingRequests.delete(key);
      return data;
    }).catch((error) => {
      this.pendingRequests.delete(key);
      throw error;
    });

    this.pendingRequests.set(key, fetchPromise);
    return fetchPromise;
  }

  /**
   * Set cache entry.
   */
  set<T>(key: string, data: T, ttl: number = this.defaultTTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  /**
   * Invalidate cache entry.
   */
  invalidate(key: string): void {
    this.cache.delete(key);
  }

  /**
   * Invalidate by pattern.
   */
  invalidatePattern(pattern: string): void {
    const regex = new RegExp(pattern);
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Clear all cache.
   */
  clear(): void {
    this.cache.clear();
    this.pendingRequests.clear();
  }

  /**
   * Get cache stats.
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys()),
    };
  }

  private async revalidate<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<void> {
    try {
      const data = await fetcher();
      this.set(key, data, ttl);
    } catch (error) {
      console.error(`Failed to revalidate cache for ${key}:`, error);
    }
  }
}

export const apiCache = new ApiCache();

/**
 * Clear API cache with optional pattern.
 */
export function clearApiCache(pattern?: string): void {
  if (pattern) {
    apiCache.invalidatePattern(pattern);
  } else {
    apiCache.clear();
  }
}

/**
 * Preload data into cache.
 */
export async function preloadData<T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl?: number
): Promise<void> {
  try {
    const data = await fetcher();
    apiCache.set(key, data, ttl);
  } catch (error) {
    console.error(`Failed to preload data for ${key}:`, error);
  }
}


/**
 * Session storage cache for larger data.
 */
export class SessionCache {
  private prefix = 'logi_cache_';

  set<T>(key: string, data: T, ttl: number = 30 * 60 * 1000): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      ttl,
    };
    try {
      sessionStorage.setItem(
        this.prefix + key,
        JSON.stringify(entry)
      );
    } catch (error) {
      console.warn('Session storage full, clearing old entries');
      this.clearExpired();
    }
  }

  get<T>(key: string): T | null {
    try {
      const item = sessionStorage.getItem(this.prefix + key);
      if (!item) return null;

      const entry: CacheEntry<T> = JSON.parse(item);
      const now = Date.now();

      if (now - entry.timestamp > entry.ttl) {
        this.delete(key);
        return null;
      }

      return entry.data;
    } catch {
      return null;
    }
  }

  delete(key: string): void {
    sessionStorage.removeItem(this.prefix + key);
  }

  clearExpired(): void {
    const now = Date.now();
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        try {
          const item = sessionStorage.getItem(key);
          if (item) {
            const entry: CacheEntry<any> = JSON.parse(item);
            if (now - entry.timestamp > entry.ttl) {
              sessionStorage.removeItem(key);
            }
          }
        } catch {
          sessionStorage.removeItem(key!);
        }
      }
    }
  }

  clear(): void {
    const keysToRemove: string[] = [];
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i);
      if (key?.startsWith(this.prefix)) {
        keysToRemove.push(key);
      }
    }
    keysToRemove.forEach((key) => sessionStorage.removeItem(key));
  }
}

export const sessionCache = new SessionCache();

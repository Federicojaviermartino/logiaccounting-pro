/**
 * Performance utilities for frontend optimization.
 */

export { apiCache, clearApiCache, preloadData } from './cache';
export { debounce, throttle, memoize } from './optimization';
export { virtualScroll, infiniteScroll } from './virtualization';
export { lazyLoad, preloadComponent } from './lazy-loading';
export { measurePerformance, trackWebVitals } from './metrics';

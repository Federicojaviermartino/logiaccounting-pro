/**
 * Performance metrics and Web Vitals tracking.
 */

export interface PerformanceMark {
  name: string;
  startTime: number;
  duration?: number;
}

export interface WebVitals {
  lcp?: number;
  fid?: number;
  cls?: number;
  fcp?: number;
  ttfb?: number;
}

/**
 * Measure performance of a function.
 */
export function measurePerformance<T>(
  name: string,
  fn: () => T
): T {
  if (typeof performance === 'undefined') {
    return fn();
  }

  const startMark = `${name}-start`;
  const endMark = `${name}-end`;

  performance.mark(startMark);
  const result = fn();
  performance.mark(endMark);

  performance.measure(name, startMark, endMark);

  const entries = performance.getEntriesByName(name);
  if (entries.length > 0) {
    console.debug(`[Performance] ${name}: ${entries[0].duration.toFixed(2)}ms`);
  }

  performance.clearMarks(startMark);
  performance.clearMarks(endMark);
  performance.clearMeasures(name);

  return result;
}

/**
 * Measure async performance.
 */
export async function measureAsyncPerformance<T>(
  name: string,
  fn: () => Promise<T>
): Promise<T> {
  if (typeof performance === 'undefined') {
    return fn();
  }

  const startMark = `${name}-start`;
  const endMark = `${name}-end`;

  performance.mark(startMark);
  const result = await fn();
  performance.mark(endMark);

  performance.measure(name, startMark, endMark);

  const entries = performance.getEntriesByName(name);
  if (entries.length > 0) {
    console.debug(`[Performance] ${name}: ${entries[0].duration.toFixed(2)}ms`);
  }

  performance.clearMarks(startMark);
  performance.clearMarks(endMark);
  performance.clearMeasures(name);

  return result;
}

/**
 * Track Web Vitals metrics.
 */
export function trackWebVitals(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof window === 'undefined') return;

  trackLCP(onReport);
  trackFID(onReport);
  trackCLS(onReport);
  trackFCP(onReport);
  trackTTFB(onReport);
}

function getRating(name: string, value: number): string {
  const thresholds: Record<string, [number, number]> = {
    LCP: [2500, 4000],
    FID: [100, 300],
    CLS: [0.1, 0.25],
    FCP: [1800, 3000],
    TTFB: [800, 1800],
  };

  const [good, needsImprovement] = thresholds[name] || [0, 0];

  if (value <= good) return 'good';
  if (value <= needsImprovement) return 'needs-improvement';
  return 'poor';
}

function trackLCP(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof PerformanceObserver === 'undefined') return;

  try {
    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1];

      if (lastEntry) {
        const value = lastEntry.startTime;
        onReport({
          name: 'LCP',
          value,
          rating: getRating('LCP', value),
        });
      }
    });

    observer.observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {
    // LCP not supported
  }
}

function trackFID(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof PerformanceObserver === 'undefined') return;

  try {
    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const firstEntry = entries[0] as PerformanceEventTiming;

      if (firstEntry) {
        const value = firstEntry.processingStart - firstEntry.startTime;
        onReport({
          name: 'FID',
          value,
          rating: getRating('FID', value),
        });
      }
    });

    observer.observe({ type: 'first-input', buffered: true });
  } catch (e) {
    // FID not supported
  }
}

function trackCLS(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof PerformanceObserver === 'undefined') return;

  let clsValue = 0;
  let sessionValue = 0;
  let sessionEntries: PerformanceEntry[] = [];

  try {
    const observer = new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries()) {
        const layoutShift = entry as any;

        if (!layoutShift.hadRecentInput) {
          const firstEntry = sessionEntries[0] as any;
          const lastEntry = sessionEntries[sessionEntries.length - 1] as any;

          if (
            sessionEntries.length &&
            entry.startTime - lastEntry.startTime < 1000 &&
            entry.startTime - firstEntry.startTime < 5000
          ) {
            sessionValue += layoutShift.value;
            sessionEntries.push(entry);
          } else {
            sessionValue = layoutShift.value;
            sessionEntries = [entry];
          }

          if (sessionValue > clsValue) {
            clsValue = sessionValue;
            onReport({
              name: 'CLS',
              value: clsValue,
              rating: getRating('CLS', clsValue),
            });
          }
        }
      }
    });

    observer.observe({ type: 'layout-shift', buffered: true });
  } catch (e) {
    // CLS not supported
  }
}

function trackFCP(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof PerformanceObserver === 'undefined') return;

  try {
    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntriesByName('first-contentful-paint');

      if (entries.length > 0) {
        const value = entries[0].startTime;
        onReport({
          name: 'FCP',
          value,
          rating: getRating('FCP', value),
        });
      }
    });

    observer.observe({ type: 'paint', buffered: true });
  } catch (e) {
    // FCP not supported
  }
}

function trackTTFB(
  onReport: (metric: { name: string; value: number; rating: string }) => void
): void {
  if (typeof performance === 'undefined') return;

  try {
    const navigationEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;

    if (navigationEntry) {
      const value = navigationEntry.responseStart - navigationEntry.requestStart;
      onReport({
        name: 'TTFB',
        value,
        rating: getRating('TTFB', value),
      });
    }
  } catch (e) {
    // TTFB not supported
  }
}

/**
 * Performance monitoring class.
 */
export class PerformanceMonitor {
  private marks: Map<string, number> = new Map();
  private measures: PerformanceMark[] = [];
  private maxMeasures = 100;

  start(name: string): void {
    this.marks.set(name, performance.now());
  }

  end(name: string): number | null {
    const startTime = this.marks.get(name);
    if (startTime === undefined) return null;

    const duration = performance.now() - startTime;
    this.marks.delete(name);

    this.measures.push({ name, startTime, duration });

    if (this.measures.length > this.maxMeasures) {
      this.measures.shift();
    }

    return duration;
  }

  getMeasures(): PerformanceMark[] {
    return [...this.measures];
  }

  getAverages(): Map<string, number> {
    const sums = new Map<string, { total: number; count: number }>();

    for (const measure of this.measures) {
      const existing = sums.get(measure.name) || { total: 0, count: 0 };
      existing.total += measure.duration || 0;
      existing.count += 1;
      sums.set(measure.name, existing);
    }

    const averages = new Map<string, number>();
    for (const [name, { total, count }] of sums) {
      averages.set(name, total / count);
    }

    return averages;
  }

  clear(): void {
    this.marks.clear();
    this.measures = [];
  }
}

export const performanceMonitor = new PerformanceMonitor();

interface PerformanceEventTiming extends PerformanceEntry {
  processingStart: number;
}

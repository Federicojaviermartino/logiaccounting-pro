/**
 * Lazy loading utilities for components and resources.
 */

import { ComponentType, lazy, LazyExoticComponent } from 'react';

type LazyComponentModule<T> = { default: ComponentType<T> };

/**
 * Create lazy loaded component with retry logic.
 */
export function lazyLoad<T extends ComponentType<any>>(
  importFn: () => Promise<LazyComponentModule<T>>,
  options: {
    retries?: number;
    delay?: number;
    onError?: (error: Error) => void;
  } = {}
): LazyExoticComponent<T> {
  const { retries = 3, delay = 1000, onError } = options;

  return lazy(() => retryImport(importFn, retries, delay, onError) as Promise<LazyComponentModule<T>>);
}

async function retryImport<T>(
  importFn: () => Promise<T>,
  retries: number,
  delay: number,
  onError?: (error: Error) => void
): Promise<T> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      return await importFn();
    } catch (error) {
      if (attempt === retries - 1) {
        if (onError && error instanceof Error) {
          onError(error);
        }
        throw error;
      }

      await new Promise((resolve) => setTimeout(resolve, delay * (attempt + 1)));
    }
  }

  throw new Error('Failed to load component');
}

/**
 * Preload component for faster navigation.
 */
export function preloadComponent(
  importFn: () => Promise<{ default: ComponentType<any> }>
): void {
  importFn().catch(() => {
    // Silently fail preload
  });
}

/**
 * Create intersection observer for lazy loading.
 */
export function createLazyObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options: IntersectionObserverInit = {}
): IntersectionObserver | null {
  if (typeof IntersectionObserver === 'undefined') {
    return null;
  }

  const defaultOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: '50px',
    threshold: 0.1,
    ...options,
  };

  return new IntersectionObserver(callback, defaultOptions);
}

/**
 * Lazy load images with intersection observer.
 */
export function lazyLoadImage(
  img: HTMLImageElement,
  src: string,
  options: {
    placeholder?: string;
    onLoad?: () => void;
    onError?: () => void;
  } = {}
): () => void {
  const { placeholder, onLoad, onError } = options;

  if (placeholder) {
    img.src = placeholder;
  }

  const observer = createLazyObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const targetImg = entry.target as HTMLImageElement;
        targetImg.src = src;

        targetImg.onload = () => {
          onLoad?.();
        };

        targetImg.onerror = () => {
          onError?.();
        };

        observer?.unobserve(targetImg);
      }
    });
  });

  if (observer) {
    observer.observe(img);
  } else {
    img.src = src;
  }

  return () => {
    observer?.disconnect();
  };
}

/**
 * Prefetch resources for faster navigation.
 */
export function prefetchResources(urls: string[]): void {
  if (typeof document === 'undefined') return;

  urls.forEach((url) => {
    const link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    link.as = url.endsWith('.js') ? 'script' : 'fetch';
    document.head.appendChild(link);
  });
}

/**
 * Preconnect to origins for faster requests.
 */
export function preconnect(origins: string[]): void {
  if (typeof document === 'undefined') return;

  origins.forEach((origin) => {
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = origin;
    link.crossOrigin = 'anonymous';
    document.head.appendChild(link);
  });
}

/**
 * Dynamic import with chunk naming.
 */
export function dynamicImport<T>(
  importFn: () => Promise<T>,
  chunkName: string
): Promise<T> {
  // The chunkName is used by webpack magic comments
  // This function provides a cleaner API
  return importFn();
}

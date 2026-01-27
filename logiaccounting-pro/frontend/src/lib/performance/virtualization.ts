/**
 * Virtualization utilities for large lists.
 */

export interface VirtualScrollOptions {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
  estimatedItemSize?: number;
}

export interface VirtualScrollResult {
  startIndex: number;
  endIndex: number;
  visibleItems: number;
  totalHeight: number;
  offsetTop: number;
}

/**
 * Calculate virtual scroll indices.
 */
export function virtualScroll(
  scrollTop: number,
  totalItems: number,
  options: VirtualScrollOptions
): VirtualScrollResult {
  const { itemHeight, containerHeight, overscan = 3 } = options;

  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
  const endIndex = Math.min(
    totalItems - 1,
    startIndex + visibleCount + overscan * 2
  );

  return {
    startIndex,
    endIndex,
    visibleItems: endIndex - startIndex + 1,
    totalHeight: totalItems * itemHeight,
    offsetTop: startIndex * itemHeight,
  };
}

export interface InfiniteScrollOptions {
  threshold?: number;
  rootMargin?: string;
}

/**
 * Create infinite scroll observer.
 */
export function infiniteScroll(
  element: HTMLElement,
  onLoadMore: () => void,
  options: InfiniteScrollOptions = {}
): () => void {
  const { threshold = 0.5, rootMargin = '100px' } = options;

  if (typeof IntersectionObserver === 'undefined') {
    console.warn('IntersectionObserver not supported');
    return () => {};
  }

  const observer = new IntersectionObserver(
    (entries) => {
      const target = entries[0];
      if (target.isIntersecting) {
        onLoadMore();
      }
    },
    {
      root: null,
      rootMargin,
      threshold,
    }
  );

  observer.observe(element);

  return () => {
    observer.disconnect();
  };
}

/**
 * Virtual list implementation with variable height support.
 */
export class VirtualList<T> {
  private items: T[] = [];
  private itemHeights: Map<number, number> = new Map();
  private defaultHeight: number;
  private containerHeight: number;
  private overscan: number;

  constructor(options: {
    defaultHeight: number;
    containerHeight: number;
    overscan?: number;
  }) {
    this.defaultHeight = options.defaultHeight;
    this.containerHeight = options.containerHeight;
    this.overscan = options.overscan || 3;
  }

  setItems(items: T[]): void {
    this.items = items;
  }

  setItemHeight(index: number, height: number): void {
    this.itemHeights.set(index, height);
  }

  getItemHeight(index: number): number {
    return this.itemHeights.get(index) || this.defaultHeight;
  }

  getTotalHeight(): number {
    let total = 0;
    for (let i = 0; i < this.items.length; i++) {
      total += this.getItemHeight(i);
    }
    return total;
  }

  getVisibleRange(scrollTop: number): { start: number; end: number; offset: number } {
    let accumulatedHeight = 0;
    let start = 0;

    for (let i = 0; i < this.items.length; i++) {
      const height = this.getItemHeight(i);
      if (accumulatedHeight + height > scrollTop) {
        start = Math.max(0, i - this.overscan);
        break;
      }
      accumulatedHeight += height;
    }

    let visibleHeight = 0;
    let end = start;

    for (let i = start; i < this.items.length; i++) {
      visibleHeight += this.getItemHeight(i);
      end = i;
      if (visibleHeight > this.containerHeight + this.defaultHeight * this.overscan * 2) {
        break;
      }
    }

    end = Math.min(this.items.length - 1, end + this.overscan);

    let offset = 0;
    for (let i = 0; i < start; i++) {
      offset += this.getItemHeight(i);
    }

    return { start, end, offset };
  }

  getVisibleItems(scrollTop: number): { items: T[]; offset: number } {
    const { start, end, offset } = this.getVisibleRange(scrollTop);
    return {
      items: this.items.slice(start, end + 1),
      offset,
    };
  }
}

/**
 * Windowing for large tables.
 */
export interface WindowedTableOptions {
  rowHeight: number;
  headerHeight: number;
  containerHeight: number;
  overscan?: number;
}

export function windowedTable(
  scrollTop: number,
  totalRows: number,
  options: WindowedTableOptions
): {
  startRow: number;
  endRow: number;
  offsetTop: number;
  totalHeight: number;
} {
  const { rowHeight, headerHeight, containerHeight, overscan = 5 } = options;

  const availableHeight = containerHeight - headerHeight;
  const visibleRows = Math.ceil(availableHeight / rowHeight);

  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscan);
  const endRow = Math.min(totalRows - 1, startRow + visibleRows + overscan * 2);

  return {
    startRow,
    endRow,
    offsetTop: startRow * rowHeight,
    totalHeight: totalRows * rowHeight + headerHeight,
  };
}

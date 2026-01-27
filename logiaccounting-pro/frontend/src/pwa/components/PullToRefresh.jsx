/**
 * PullToRefresh - Pull down to refresh content
 */

import React, { useState, useRef, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';

const THRESHOLD = 80;
const MAX_PULL = 120;

export default function PullToRefresh({ onRefresh, children }) {
  const [pulling, setPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const startY = useRef(0);
  const containerRef = useRef(null);

  const handleTouchStart = useCallback((e) => {
    if (containerRef.current?.scrollTop === 0) {
      startY.current = e.touches[0].clientY;
      setPulling(true);
    }
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!pulling || refreshing) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;

    if (diff > 0) {
      e.preventDefault();
      const distance = Math.min(diff * 0.5, MAX_PULL);
      setPullDistance(distance);
    }
  }, [pulling, refreshing]);

  const handleTouchEnd = useCallback(async () => {
    if (!pulling) return;

    if (pullDistance >= THRESHOLD && !refreshing) {
      setRefreshing(true);
      setPullDistance(60);

      try {
        await onRefresh();
      } finally {
        setRefreshing(false);
        setPullDistance(0);
      }
    } else {
      setPullDistance(0);
    }

    setPulling(false);
  }, [pulling, pullDistance, refreshing, onRefresh]);

  const progress = Math.min(pullDistance / THRESHOLD, 1);
  const rotation = progress * 180;

  return (
    <div
      ref={containerRef}
      className="h-full overflow-y-auto overscroll-contain"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <div
        className="flex items-center justify-center transition-all duration-200
                   overflow-hidden"
        style={{ height: pullDistance }}
      >
        <RefreshCw
          className={`w-6 h-6 text-blue-600 transition-transform
                     ${refreshing ? 'animate-spin' : ''}`}
          style={{ transform: `rotate(${rotation}deg)` }}
        />
      </div>

      {/* Content */}
      <div
        className="transition-transform duration-200"
        style={{ transform: `translateY(${pulling ? 0 : 0}px)` }}
      >
        {children}
      </div>
    </div>
  );
}

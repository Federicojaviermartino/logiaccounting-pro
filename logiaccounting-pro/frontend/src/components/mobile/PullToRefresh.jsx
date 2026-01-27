/**
 * Pull to Refresh - Touch gesture refresh component
 */

import React, { useState, useRef, useCallback } from 'react';
import { RefreshCw } from 'lucide-react';

const THRESHOLD = 80;
const RESISTANCE = 2.5;

export default function PullToRefresh({ onRefresh, children, disabled = false }) {
  const [pullDistance, setPullDistance] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const containerRef = useRef(null);
  const startY = useRef(0);
  const isPulling = useRef(false);

  const handleTouchStart = useCallback((e) => {
    if (disabled || isRefreshing) return;

    const container = containerRef.current;
    if (container && container.scrollTop === 0) {
      startY.current = e.touches[0].clientY;
      isPulling.current = true;
    }
  }, [disabled, isRefreshing]);

  const handleTouchMove = useCallback((e) => {
    if (!isPulling.current || disabled || isRefreshing) return;

    const currentY = e.touches[0].clientY;
    const diff = currentY - startY.current;

    if (diff > 0) {
      // Apply resistance
      const distance = Math.min(diff / RESISTANCE, 120);
      setPullDistance(distance);

      // Prevent scroll while pulling
      if (distance > 10) {
        e.preventDefault();
      }
    }
  }, [disabled, isRefreshing]);

  const handleTouchEnd = useCallback(async () => {
    if (!isPulling.current || disabled) return;

    isPulling.current = false;

    if (pullDistance >= THRESHOLD && onRefresh) {
      setIsRefreshing(true);

      try {
        await onRefresh();
      } finally {
        setIsRefreshing(false);
      }
    }

    setPullDistance(0);
  }, [pullDistance, onRefresh, disabled]);

  const progress = Math.min(pullDistance / THRESHOLD, 1);
  const shouldTrigger = pullDistance >= THRESHOLD;

  return (
    <div
      ref={containerRef}
      className="pull-to-refresh-container"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* Pull indicator */}
      <div
        className={`pull-indicator ${isRefreshing ? 'refreshing' : ''} ${shouldTrigger ? 'ready' : ''}`}
        style={{
          transform: `translateY(${pullDistance - 60}px)`,
          opacity: progress,
        }}
      >
        <div
          className="indicator-content"
          style={{
            transform: `rotate(${progress * 180}deg)`,
          }}
        >
          <RefreshCw className={`icon ${isRefreshing ? 'spinning' : ''}`} />
        </div>
        <span className="indicator-text">
          {isRefreshing ? 'Refreshing...' : shouldTrigger ? 'Release to refresh' : 'Pull to refresh'}
        </span>
      </div>

      {/* Content */}
      <div
        className="pull-content"
        style={{
          transform: pullDistance > 0 ? `translateY(${pullDistance}px)` : undefined,
        }}
      >
        {children}
      </div>

      <style jsx>{`
        .pull-to-refresh-container {
          position: relative;
          overflow-y: auto;
          overflow-x: hidden;
          height: 100%;
          -webkit-overflow-scrolling: touch;
        }

        .pull-indicator {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 60px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 8px;
          z-index: 10;
          pointer-events: none;
        }

        .indicator-content {
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .icon {
          width: 24px;
          height: 24px;
          color: var(--primary);
          transition: color 0.2s;
        }

        .pull-indicator.ready .icon {
          color: var(--success);
        }

        .icon.spinning {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }

        .indicator-text {
          font-size: 12px;
          color: var(--text-muted);
          font-weight: 500;
        }

        .pull-indicator.ready .indicator-text {
          color: var(--success);
        }

        .pull-content {
          transition: transform 0.2s ease-out;
          min-height: 100%;
        }

        @media (min-width: 769px) {
          .pull-indicator {
            display: none;
          }
        }
      `}</style>
    </div>
  );
}

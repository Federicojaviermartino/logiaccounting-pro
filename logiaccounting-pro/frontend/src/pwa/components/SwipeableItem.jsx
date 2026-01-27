/**
 * SwipeableItem - Swipe to reveal actions
 */

import React, { useState, useRef } from 'react';

const SWIPE_THRESHOLD = 80;

export default function SwipeableItem({
  children,
  leftActions,
  rightActions,
  onSwipeLeft,
  onSwipeRight,
}) {
  const [offsetX, setOffsetX] = useState(0);
  const [isSwiping, setIsSwiping] = useState(false);
  const startX = useRef(0);
  const currentX = useRef(0);

  const handleTouchStart = (e) => {
    startX.current = e.touches[0].clientX;
    currentX.current = startX.current;
    setIsSwiping(true);
  };

  const handleTouchMove = (e) => {
    if (!isSwiping) return;

    currentX.current = e.touches[0].clientX;
    const diff = currentX.current - startX.current;

    // Limit swipe distance
    const maxLeft = rightActions ? -150 : 0;
    const maxRight = leftActions ? 150 : 0;

    const newOffset = Math.max(maxLeft, Math.min(maxRight, diff));
    setOffsetX(newOffset);
  };

  const handleTouchEnd = () => {
    setIsSwiping(false);

    if (Math.abs(offsetX) >= SWIPE_THRESHOLD) {
      if (offsetX > 0 && onSwipeRight) {
        onSwipeRight();
      } else if (offsetX < 0 && onSwipeLeft) {
        onSwipeLeft();
      }
    }

    // Snap to reveal actions or reset
    if (offsetX > SWIPE_THRESHOLD && leftActions) {
      setOffsetX(100);
    } else if (offsetX < -SWIPE_THRESHOLD && rightActions) {
      setOffsetX(-100);
    } else {
      setOffsetX(0);
    }
  };

  const resetPosition = () => setOffsetX(0);

  return (
    <div className="relative overflow-hidden">
      {/* Left actions */}
      {leftActions && (
        <div
          className="absolute inset-y-0 left-0 flex items-center bg-green-500"
          style={{ width: Math.max(0, offsetX) }}
        >
          {leftActions}
        </div>
      )}

      {/* Right actions */}
      {rightActions && (
        <div
          className="absolute inset-y-0 right-0 flex items-center bg-red-500"
          style={{ width: Math.max(0, -offsetX) }}
        >
          {rightActions}
        </div>
      )}

      {/* Content */}
      <div
        className={`relative bg-white transition-transform ${
          isSwiping ? '' : 'duration-200'
        }`}
        style={{ transform: `translateX(${offsetX}px)` }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        onClick={offsetX !== 0 ? resetPosition : undefined}
      >
        {children}
      </div>
    </div>
  );
}

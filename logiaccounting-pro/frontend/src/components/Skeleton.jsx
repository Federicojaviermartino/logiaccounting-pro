/**
 * Skeleton loading components for better perceived performance
 */

// Base skeleton with shimmer effect
export function Skeleton({ width, height, borderRadius = '4px', className = '' }) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width: width || '100%',
        height: height || '20px',
        borderRadius
      }}
    />
  );
}

// Text line skeleton
export function SkeletonText({ lines = 3, width = '100%' }) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? '70%' : width}
          height="16px"
          className="skeleton-line"
        />
      ))}
    </div>
  );
}

// Card skeleton
export function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <Skeleton height="120px" borderRadius="8px" />
      <div className="skeleton-card-content">
        <Skeleton width="60%" height="20px" />
        <Skeleton width="40%" height="16px" />
        <Skeleton width="80%" height="14px" />
      </div>
    </div>
  );
}

// Table skeleton
export function SkeletonTable({ rows = 5, columns = 4 }) {
  return (
    <div className="skeleton-table">
      {/* Header */}
      <div className="skeleton-table-header">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} height="20px" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="skeleton-table-row">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} height="16px" />
          ))}
        </div>
      ))}
    </div>
  );
}

// Stats card skeleton
export function SkeletonStats({ count = 4 }) {
  return (
    <div className="stats-grid">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="stat-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Skeleton width="100px" height="14px" />
            <Skeleton width="40px" height="40px" borderRadius="8px" />
          </div>
          <Skeleton width="80px" height="32px" style={{ marginTop: '8px' }} />
          <Skeleton width="120px" height="12px" style={{ marginTop: '4px' }} />
        </div>
      ))}
    </div>
  );
}

// Chart skeleton
export function SkeletonChart({ height = '300px' }) {
  return (
    <div className="skeleton-chart" style={{ height }}>
      <Skeleton height="100%" borderRadius="8px" />
    </div>
  );
}

// Dashboard skeleton
export function SkeletonDashboard() {
  return (
    <div className="skeleton-dashboard">
      <SkeletonStats count={4} />
      <div className="grid-2" style={{ marginTop: '24px' }}>
        <div className="card">
          <Skeleton width="150px" height="24px" style={{ marginBottom: '16px' }} />
          <SkeletonChart height="250px" />
        </div>
        <div className="card">
          <Skeleton width="150px" height="24px" style={{ marginBottom: '16px' }} />
          <SkeletonTable rows={5} columns={3} />
        </div>
      </div>
    </div>
  );
}

export default Skeleton;

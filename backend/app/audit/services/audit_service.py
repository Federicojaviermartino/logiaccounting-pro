"""Audit logging service."""
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import Session

from app.audit.models.audit_log import AuditLog, DataChangeLog, EntitySnapshot, AuditAction, AuditSeverity
from app.audit.schemas.audit import (
    AuditLogCreate, AuditLogResponse, AuditLogFilter, AuditSummary
)


class AuditService:
    """Service for audit logging and retrieval."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def log(
        self,
        customer_id: UUID,
        action: AuditAction,
        resource_type: str,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_name: Optional[str] = None,
        description: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        metadata: Optional[dict] = None,
        severity: AuditSeverity = AuditSeverity.LOW,
        is_sensitive: bool = False
    ) -> AuditLog:
        """Create an audit log entry."""
        changed_fields = None
        if old_values and new_values:
            changed_fields = self._get_changed_fields(old_values, new_values)
        
        audit_log = AuditLog(
            id=uuid4(),
            customer_id=customer_id,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            user_role=user_role,
            action=action,
            severity=severity,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            description=description,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            session_id=session_id,
            endpoint=endpoint,
            http_method=http_method,
            metadata=metadata,
            is_sensitive=is_sensitive
        )
        
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        
        if old_values and new_values and changed_fields:
            await self._log_field_changes(
                audit_log_id=audit_log.id,
                customer_id=customer_id,
                table_name=resource_type,
                record_id=resource_id,
                old_values=old_values,
                new_values=new_values,
                changed_fields=changed_fields
            )
        
        return audit_log
    
    async def log_create(
        self,
        customer_id: UUID,
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        new_values: Optional[dict] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Log a create action."""
        return await self.log(
            customer_id=customer_id,
            action=AuditAction.CREATE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            new_values=new_values,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            description=f"Created {resource_type}: {resource_name or resource_id}",
            **kwargs
        )
    
    async def log_update(
        self,
        customer_id: UUID,
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Log an update action."""
        changed_fields = self._get_changed_fields(old_values or {}, new_values or {})
        description = f"Updated {resource_type}: {resource_name or resource_id}"
        if changed_fields:
            description += f" (fields: {', '.join(changed_fields[:5])})"
        
        return await self.log(
            customer_id=customer_id,
            action=AuditAction.UPDATE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values,
            new_values=new_values,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            description=description,
            severity=AuditSeverity.MEDIUM,
            **kwargs
        )
    
    async def log_delete(
        self,
        customer_id: UUID,
        resource_type: str,
        resource_id: str,
        resource_name: Optional[str] = None,
        old_values: Optional[dict] = None,
        user_id: Optional[UUID] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Log a delete action."""
        return await self.log(
            customer_id=customer_id,
            action=AuditAction.DELETE,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            old_values=old_values,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            description=f"Deleted {resource_type}: {resource_name or resource_id}",
            severity=AuditSeverity.HIGH,
            **kwargs
        )
    
    async def log_login(
        self,
        customer_id: Optional[UUID],
        user_id: UUID,
        user_email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        **kwargs
    ) -> AuditLog:
        """Log a login attempt."""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        
        description = f"User {user_email} logged in successfully" if success else \
                      f"Failed login attempt for {user_email}: {failure_reason}"
        
        return await self.log(
            customer_id=customer_id,
            action=action,
            resource_type="user",
            resource_id=str(user_id),
            user_id=user_id if success else None,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            severity=severity,
            metadata={"failure_reason": failure_reason} if failure_reason else None,
            **kwargs
        )
    
    async def get_logs(
        self,
        customer_id: UUID,
        filters: AuditLogFilter,
        page: int = 1,
        page_size: int = 50
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs with filtering and pagination."""
        query = select(AuditLog).where(AuditLog.customer_id == customer_id)
        
        if filters.start_date:
            query = query.where(AuditLog.timestamp >= filters.start_date)
        if filters.end_date:
            query = query.where(AuditLog.timestamp <= filters.end_date)
        if filters.user_id:
            query = query.where(AuditLog.user_id == filters.user_id)
        if filters.action:
            query = query.where(AuditLog.action == filters.action)
        if filters.actions:
            query = query.where(AuditLog.action.in_(filters.actions))
        if filters.severity:
            query = query.where(AuditLog.severity == filters.severity)
        if filters.resource_type:
            query = query.where(AuditLog.resource_type == filters.resource_type)
        if filters.resource_id:
            query = query.where(AuditLog.resource_id == filters.resource_id)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    AuditLog.description.ilike(search_term),
                    AuditLog.resource_name.ilike(search_term),
                    AuditLog.user_email.ilike(search_term)
                )
            )
        
        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.execute(count_query).scalar()
        
        query = query.order_by(desc(AuditLog.timestamp))
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = self.db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    async def get_log_by_id(self, customer_id: UUID, log_id: UUID) -> Optional[AuditLog]:
        """Get a specific audit log entry."""
        query = select(AuditLog).where(
            AuditLog.id == log_id,
            AuditLog.customer_id == customer_id
        )
        result = self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_entity_history(
        self,
        customer_id: UUID,
        resource_type: str,
        resource_id: str
    ) -> List[AuditLog]:
        """Get complete history for an entity."""
        query = select(AuditLog).where(
            AuditLog.customer_id == customer_id,
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(desc(AuditLog.timestamp))
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_activity(
        self,
        customer_id: UUID,
        user_id: UUID,
        days: int = 30
    ) -> List[AuditLog]:
        """Get user activity for the specified period."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(AuditLog).where(
            AuditLog.customer_id == customer_id,
            AuditLog.user_id == user_id,
            AuditLog.timestamp >= start_date
        ).order_by(desc(AuditLog.timestamp))
        
        result = self.db.execute(query)
        return result.scalars().all()
    
    async def get_summary(
        self,
        customer_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> AuditSummary:
        """Get audit summary for a period."""
        base_query = select(AuditLog).where(
            AuditLog.customer_id == customer_id,
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
        
        total = self.db.execute(
            select(func.count()).select_from(base_query.subquery())
        ).scalar()
        
        action_counts = self.db.execute(
            select(AuditLog.action, func.count()).where(
                AuditLog.customer_id == customer_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.action)
        ).all()
        events_by_action = {str(row[0].value): row[1] for row in action_counts}
        
        severity_counts = self.db.execute(
            select(AuditLog.severity, func.count()).where(
                AuditLog.customer_id == customer_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.severity)
        ).all()
        events_by_severity = {str(row[0].value): row[1] for row in severity_counts}
        
        resource_counts = self.db.execute(
            select(AuditLog.resource_type, func.count()).where(
                AuditLog.customer_id == customer_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date
            ).group_by(AuditLog.resource_type)
        ).all()
        events_by_resource = {row[0]: row[1] for row in resource_counts}
        
        top_users_query = self.db.execute(
            select(AuditLog.user_email, func.count().label('count')).where(
                AuditLog.customer_id == customer_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                AuditLog.user_email.isnot(None)
            ).group_by(AuditLog.user_email).order_by(desc('count')).limit(10)
        ).all()
        top_users = [{"email": row[0], "count": row[1]} for row in top_users_query]
        
        critical_logs = self.db.execute(
            select(AuditLog).where(
                AuditLog.customer_id == customer_id,
                AuditLog.timestamp >= start_date,
                AuditLog.timestamp <= end_date,
                AuditLog.severity.in_([AuditSeverity.HIGH, AuditSeverity.CRITICAL])
            ).order_by(desc(AuditLog.timestamp)).limit(10)
        ).scalars().all()
        
        return AuditSummary(
            period_start=start_date,
            period_end=end_date,
            total_events=total,
            events_by_action=events_by_action,
            events_by_severity=events_by_severity,
            events_by_resource=events_by_resource,
            top_users=top_users,
            recent_critical=[AuditLogResponse.model_validate(log) for log in critical_logs]
        )
    
    async def create_snapshot(
        self,
        customer_id: UUID,
        entity_type: str,
        entity_id: str,
        snapshot_data: dict,
        audit_log_id: Optional[UUID] = None,
        reason: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> EntitySnapshot:
        """Create a snapshot of an entity."""
        snapshot = EntitySnapshot(
            id=uuid4(),
            customer_id=customer_id,
            audit_log_id=audit_log_id,
            entity_type=entity_type,
            entity_id=entity_id,
            snapshot_data=snapshot_data,
            reason=reason,
            created_by=created_by
        )
        
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        
        return snapshot
    
    async def _log_field_changes(
        self,
        audit_log_id: UUID,
        customer_id: UUID,
        table_name: str,
        record_id: str,
        old_values: dict,
        new_values: dict,
        changed_fields: List[str]
    ):
        """Log individual field changes."""
        for field in changed_fields:
            old_val = old_values.get(field)
            new_val = new_values.get(field)
            
            change_log = DataChangeLog(
                id=uuid4(),
                audit_log_id=audit_log_id,
                customer_id=customer_id,
                table_name=table_name,
                record_id=record_id,
                field_name=field,
                field_type=type(new_val).__name__ if new_val else None,
                old_value=self._serialize_value(old_val),
                new_value=self._serialize_value(new_val)
            )
            self.db.add(change_log)
        
        self.db.commit()
    
    def _get_changed_fields(self, old_values: dict, new_values: dict) -> List[str]:
        """Get list of fields that changed between two states."""
        changed = []
        all_keys = set(old_values.keys()) | set(new_values.keys())
        
        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)
            if old_val != new_val:
                changed.append(key)
        
        return changed
    
    def _serialize_value(self, value: Any) -> Optional[str]:
        """Serialize a value to string for storage."""
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        return str(value)

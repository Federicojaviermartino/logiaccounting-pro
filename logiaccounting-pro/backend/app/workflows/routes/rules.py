"""
Business rules API routes.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from app.utils.datetime_utils import utc_now
from app.routes.auth import get_current_user
from app.workflows.models.rule import BusinessRule, RuleCreate, RuleUpdate
from app.workflows.models.store import workflow_store
from app.workflows.rules.evaluator import RuleEvaluator, ExpressionEvaluator


router = APIRouter(prefix="/rules", tags=["Business Rules"])


@router.post("", response_model=dict)
async def create_rule(
    rule_data: RuleCreate,
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """Create a new business rule."""
    rule = BusinessRule(
        name=rule_data.name,
        description=rule_data.description,
        priority=rule_data.priority,
        trigger=rule_data.trigger,
        scope=rule_data.scope,
        conditions=rule_data.conditions,
        actions=rule_data.actions,
        tenant_id=tenant_id,
        created_by=current_user["id"]
    )

    workflow_store.save_rule(rule)

    return {"id": rule.id, "name": rule.name, "status": rule.status}


@router.get("", response_model=List[dict])
async def list_rules(
    status: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    current_user: dict = Depends(get_current_user),
    tenant_id: str = Query(default="default")
):
    """List business rules."""
    rules = workflow_store.get_rules_by_tenant(
        tenant_id=tenant_id,
        status=status,
        skip=skip,
        limit=limit
    )

    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "status": r.status,
            "priority": r.priority,
            "entity": r.scope.entity,
            "execution_count": r.execution_count,
            "last_executed": r.last_executed
        }
        for r in rules
    ]


@router.get("/{rule_id}", response_model=dict)
async def get_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a rule by ID."""
    rule = workflow_store.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    return rule.dict()


@router.put("/{rule_id}", response_model=dict)
async def update_rule(
    rule_id: str,
    updates: RuleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a rule."""
    rule = workflow_store.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if updates.name is not None:
        rule.name = updates.name
    if updates.description is not None:
        rule.description = updates.description
    if updates.priority is not None:
        rule.priority = updates.priority
    if updates.trigger is not None:
        rule.trigger = updates.trigger
    if updates.scope is not None:
        rule.scope = updates.scope
    if updates.conditions is not None:
        rule.conditions = updates.conditions
    if updates.actions is not None:
        rule.actions = updates.actions

    rule.version += 1
    rule.updated_at = utc_now()
    rule.updated_by = current_user["id"]

    workflow_store.save_rule(rule)

    return {"id": rule.id, "version": rule.version, "updated": True}


@router.delete("/{rule_id}")
async def delete_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a rule."""
    if not workflow_store.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")

    return {"deleted": True}


@router.post("/{rule_id}/activate")
async def activate_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Activate a rule."""
    rule = workflow_store.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.status = "active"
    workflow_store.save_rule(rule)

    return {"id": rule.id, "status": rule.status}


@router.post("/{rule_id}/pause")
async def pause_rule(
    rule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Pause a rule."""
    rule = workflow_store.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    rule.status = "paused"
    workflow_store.save_rule(rule)

    return {"id": rule.id, "status": rule.status}


@router.post("/{rule_id}/test")
async def test_rule(
    rule_id: str,
    test_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Test a rule against sample data."""
    rule = workflow_store.get_rule(rule_id)

    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    evaluator = RuleEvaluator()
    result = evaluator.evaluate(rule.dict(), test_data)

    return {
        "rule_id": rule.id,
        "matched": result,
        "test_data": test_data,
        "actions_would_execute": [a.dict() for a in rule.actions] if result else []
    }


@router.post("/evaluate")
async def evaluate_expression(
    expression: str,
    variables: dict,
    current_user: dict = Depends(get_current_user)
):
    """Evaluate an expression with variables."""
    evaluator = ExpressionEvaluator()

    try:
        result = evaluator.evaluate(expression, variables)
        return {
            "expression": expression,
            "result": result,
            "type": type(result).__name__
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e)
        }

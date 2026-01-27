"""
Error Handling Actions - Try-Catch, Retry, Fallback, Circuit Breaker
"""

from typing import Dict, Any, List
from datetime import datetime
import asyncio
import logging

from app.workflows.actions.base import ActionExecutor, ActionResult


logger = logging.getLogger(__name__)


class TryCatchAction(ActionExecutor):
    """Try-Catch block for error handling."""

    action_type = "try_catch"

    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            try_steps = config.get("try_steps", [])
            catch_steps = config.get("catch_steps", [])
            finally_steps = config.get("finally_steps", [])
            rethrow = config.get("rethrow", False)

            if not try_steps:
                return ActionResult(success=False, error="try_steps required")

            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()

            error_context = None
            try_success = True

            try:
                for step in try_steps:
                    result = await executor.execute_step(step, context)
                    if not result.success:
                        try_success = False
                        error_context = {"error": result.error, "step": step.get("name", step.get("type"))}
                        break
            except Exception as e:
                try_success = False
                error_context = {"error": str(e), "type": type(e).__name__}

            if not try_success and catch_steps:
                context["error"] = error_context
                for step in catch_steps:
                    await executor.execute_step(step, context)

            if finally_steps:
                for step in finally_steps:
                    await executor.execute_step(step, context)

            if try_success:
                return ActionResult(success=True, message="Try block completed")
            elif catch_steps and not rethrow:
                return ActionResult(success=True, data={"recovered": True, "error_context": error_context})
            else:
                return ActionResult(success=False, error=error_context.get("error"))

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class RetryAction(ActionExecutor):
    """Retry action with configurable policy."""

    action_type = "retry"

    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            action_config = config.get("action")
            max_retries = config.get("max_retries", 3)
            strategy = config.get("strategy", "exponential")
            initial_delay = config.get("initial_delay_seconds", 1)
            max_delay = config.get("max_delay_seconds", 60)

            if not action_config:
                return ActionResult(success=False, error="action required")

            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()

            attempts = []
            last_error = None

            for attempt in range(max_retries + 1):
                try:
                    result = await executor.execute_step(action_config, context)
                    attempts.append({"attempt": attempt + 1, "success": result.success})

                    if result.success:
                        return ActionResult(success=True, data={"attempts": len(attempts), **result.data})
                    last_error = result.error
                except Exception as e:
                    last_error = str(e)
                    attempts.append({"attempt": attempt + 1, "success": False, "error": last_error})

                if attempt < max_retries:
                    delay = self._calc_delay(attempt, strategy, initial_delay, max_delay)
                    await asyncio.sleep(delay)

            return ActionResult(success=False, error=f"Failed after {len(attempts)} attempts: {last_error}", data={"attempts": attempts})

        except Exception as e:
            return ActionResult(success=False, error=str(e))

    def _calc_delay(self, attempt: int, strategy: str, base: float, max_d: float) -> float:
        if strategy == "fixed":
            return min(base, max_d)
        elif strategy == "exponential":
            return min(base * (2 ** attempt), max_d)
        elif strategy == "linear":
            return min(base * (attempt + 1), max_d)
        return base


class FallbackAction(ActionExecutor):
    """Execute fallback if primary fails."""

    action_type = "fallback"

    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            primary = config.get("primary")
            fallbacks = config.get("fallbacks", [])

            if not primary:
                return ActionResult(success=False, error="primary action required")

            from app.workflows.engine.executor import WorkflowExecutor
            executor = WorkflowExecutor()

            result = await executor.execute_step(primary, context)
            if result.success:
                return ActionResult(success=True, data={**result.data, "used_fallback": False})

            primary_error = result.error

            for i, fallback in enumerate(fallbacks):
                result = await executor.execute_step(fallback, context)
                if result.success:
                    return ActionResult(success=True, data={**result.data, "used_fallback": True, "fallback_index": i})

            return ActionResult(success=False, error=f"All actions failed. Primary: {primary_error}")

        except Exception as e:
            return ActionResult(success=False, error=str(e))


class CircuitBreakerAction(ActionExecutor):
    """Circuit breaker pattern."""

    action_type = "circuit_breaker"
    _circuits: Dict[str, Dict] = {}

    async def execute(self, config: Dict[str, Any], context: Dict[str, Any]) -> ActionResult:
        try:
            circuit_id = config.get("circuit_id", "default")
            action_config = config.get("action")
            failure_threshold = config.get("failure_threshold", 5)
            reset_timeout = config.get("reset_timeout_seconds", 60)

            if not action_config:
                return ActionResult(success=False, error="action required")

            circuit = self._circuits.setdefault(circuit_id, {
                "state": "closed", "failures": 0, "last_failure": 0
            })

            if circuit["state"] == "open":
                if datetime.utcnow().timestamp() - circuit["last_failure"] > reset_timeout:
                    circuit["state"] = "half_open"
                else:
                    return ActionResult(success=False, error="Circuit breaker open", data={"circuit_state": "open"})

            from app.workflows.engine.executor import WorkflowExecutor
            result = await WorkflowExecutor().execute_step(action_config, context)

            if result.success:
                if circuit["state"] == "half_open":
                    circuit["state"] = "closed"
                circuit["failures"] = 0
                return ActionResult(success=True, data={**result.data, "circuit_state": circuit["state"]})

            circuit["failures"] += 1
            circuit["last_failure"] = datetime.utcnow().timestamp()
            if circuit["failures"] >= failure_threshold:
                circuit["state"] = "open"

            return ActionResult(success=False, error=result.error, data={"circuit_state": circuit["state"]})

        except Exception as e:
            return ActionResult(success=False, error=str(e))

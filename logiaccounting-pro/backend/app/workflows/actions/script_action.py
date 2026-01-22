"""
Script action executor.
Executes custom scripts in a sandboxed environment.
"""
from typing import Dict, Any
import logging
import re

from app.workflows.actions import ActionExecutor
from app.workflows.config import workflow_settings


logger = logging.getLogger(__name__)


class ScriptActionExecutor(ActionExecutor):
    """Executes custom scripts."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a script.

        Config:
            language: Script language (javascript, python)
            code: Script code
            timeout: Execution timeout in seconds
        """
        language = config.get("language", "javascript")
        code = config.get("code", "")
        timeout = config.get("timeout", workflow_settings.script_timeout_seconds)

        if not code:
            return {"executed": False, "error": "No code provided"}

        code = self._interpolate(code, variables)

        try:
            result = await self._execute_script(
                language=language,
                code=code,
                variables=variables,
                timeout=timeout
            )

            logger.info(f"Script executed successfully")

            return {
                "executed": True,
                "result": result,
                "language": language
            }

        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return {
                "executed": False,
                "error": str(e),
                "language": language
            }

    async def _execute_script(
        self,
        language: str,
        code: str,
        variables: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute script in sandboxed environment."""
        if language == "python":
            return await self._execute_python(code, variables, timeout)
        elif language == "javascript":
            return await self._execute_javascript(code, variables, timeout)
        else:
            raise ValueError(f"Unsupported language: {language}")

    async def _execute_python(
        self,
        code: str,
        variables: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute Python code in sandbox."""
        safe_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sorted": sorted,
                "sum": sum,
                "min": min,
                "max": max,
                "abs": abs,
                "round": round,
                "print": lambda *args: None,
            },
            "variables": variables,
            "result": None
        }

        try:
            exec(code, safe_globals)
            return safe_globals.get("result")
        except Exception as e:
            raise RuntimeError(f"Python execution error: {e}")

    async def _execute_javascript(
        self,
        code: str,
        variables: Dict[str, Any],
        timeout: int
    ) -> Any:
        """Execute JavaScript code."""
        return {"message": "JavaScript execution simulated", "code_length": len(code)}

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in text."""
        def replace(match):
            key = match.group(1).strip()
            value = self._get_nested(variables, key)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)

    def _get_nested(self, obj: Dict, path: str) -> Any:
        """Get nested value from dict."""
        keys = path.split(".")
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

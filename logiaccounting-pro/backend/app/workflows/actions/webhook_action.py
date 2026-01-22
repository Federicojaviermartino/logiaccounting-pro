"""
Webhook action executor.
Makes HTTP requests to external services.
"""
from typing import Dict, Any, Optional
import logging
import json
import re

from app.workflows.actions import ActionExecutor


logger = logging.getLogger(__name__)


class WebhookActionExecutor(ActionExecutor):
    """Executes webhook/HTTP request actions."""

    async def execute(
        self,
        config: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Make an HTTP request.

        Config:
            url: Request URL (required)
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            headers: Request headers
            body: Request body (for POST/PUT/PATCH)
            query_params: Query string parameters
            timeout: Request timeout in seconds
            retry_on_failure: Whether to retry on failure
            expected_status: Expected status code(s)
        """
        url = self._interpolate(config.get("url", ""), variables)
        method = config.get("method", "POST").upper()
        headers = self._interpolate_dict(config.get("headers", {}), variables)
        body = config.get("body")
        query_params = self._interpolate_dict(config.get("query_params", {}), variables)
        timeout = config.get("timeout", 30)
        expected_status = config.get("expected_status", [200, 201, 202, 204])

        if isinstance(expected_status, int):
            expected_status = [expected_status]

        if body:
            if isinstance(body, dict):
                body = self._interpolate_dict(body, variables)
                body = json.dumps(body)
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"
            else:
                body = self._interpolate(str(body), variables)

        try:
            import httpx

            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=query_params,
                    content=body
                )

            success = response.status_code in expected_status

            try:
                response_body = response.json()
            except:
                response_body = response.text

            result = {
                "success": success,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
                "url": url,
                "method": method
            }

            if not success:
                logger.warning(
                    f"Webhook returned unexpected status: {response.status_code}"
                )

            return result

        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "method": method
            }

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in text."""
        def replace(match):
            key = match.group(1).strip()
            value = self._get_nested(variables, key)
            return str(value) if value is not None else match.group(0)

        return re.sub(r'\{\{([^}]+)\}\}', replace, text)

    def _interpolate_dict(
        self,
        obj: Dict[str, Any],
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpolate variables in dictionary values."""
        result = {}

        for key, value in obj.items():
            if isinstance(value, str):
                result[key] = self._interpolate(value, variables)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict(value, variables)
            else:
                result[key] = value

        return result

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

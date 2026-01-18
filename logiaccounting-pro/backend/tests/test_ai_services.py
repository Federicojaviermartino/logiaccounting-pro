"""
AI Services endpoint tests
"""
import pytest


class TestCashFlowPredictor:
    """Cash flow prediction tests"""

    def test_get_prediction_default(self, client, admin_headers):
        """Test getting default 90-day prediction"""
        response = client.get("/api/v1/cashflow/predict", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert "summary" in data

    def test_get_prediction_30_days(self, client, admin_headers):
        """Test getting 30-day prediction"""
        response = client.get(
            "/api/v1/cashflow/predict?days=30",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("predictions", [])) <= 30

    def test_prediction_forbidden_for_supplier(self, client, supplier_headers):
        """Test supplier cannot access cash flow predictions"""
        response = client.get("/api/v1/cashflow/predict", headers=supplier_headers)
        assert response.status_code == 403


class TestAnomalyDetection:
    """Anomaly detection tests"""

    def test_run_scan(self, client, admin_headers):
        """Test running anomaly scan"""
        response = client.get("/api/v1/anomaly/scan", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_anomalies" in data
        assert "anomalies" in data
        assert "risk_score" in data

    def test_get_summary(self, client, admin_headers):
        """Test getting anomaly summary"""
        response = client.get("/api/v1/anomaly/summary", headers=admin_headers)
        assert response.status_code == 200

    def test_check_transaction(self, client, admin_headers):
        """Test checking single transaction"""
        response = client.post(
            "/api/v1/anomaly/check-transaction",
            json={
                "amount": 1500.00,
                "vendor_name": "Test Vendor",
                "description": "Test transaction"
            },
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "transaction_ok" in data

    def test_anomaly_scan_forbidden_for_client(self, client, client_headers):
        """Test client cannot run anomaly scan"""
        response = client.get("/api/v1/anomaly/scan", headers=client_headers)
        assert response.status_code == 403

    def test_get_status(self, client, admin_headers):
        """Test getting anomaly service status"""
        response = client.get("/api/v1/anomaly/status", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "ml_detection_enabled" in data


class TestPaymentScheduler:
    """Payment scheduler tests"""

    def test_optimize_schedule(self, client, admin_headers):
        """Test getting optimized payment schedule"""
        response = client.get(
            "/api/v1/scheduler/optimize?available_cash=50000",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    def test_optimize_different_strategies(self, client, admin_headers):
        """Test different optimization strategies"""
        strategies = ["balanced", "minimize_cost", "maximize_discount"]
        for strategy in strategies:
            response = client.get(
                f"/api/v1/scheduler/optimize?optimize_for={strategy}",
                headers=admin_headers
            )
            assert response.status_code == 200


class TestAssistant:
    """Profitability assistant tests"""

    def test_query_assistant(self, client, admin_headers):
        """Test querying the assistant"""
        response = client.post(
            "/api/v1/assistant/query",
            json={"query": "What projects are over budget?"},
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

    def test_get_suggestions(self, client, admin_headers):
        """Test getting query suggestions"""
        response = client.get("/api/v1/assistant/suggestions", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

    def test_assistant_status(self, client, admin_headers):
        """Test getting assistant status"""
        response = client.get("/api/v1/assistant/status", headers=admin_headers)
        assert response.status_code == 200


class TestOCR:
    """OCR service tests"""

    def test_get_ocr_status(self, client, admin_headers):
        """Test getting OCR service status"""
        response = client.get("/api/v1/ocr/status", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "tesseract_available" in data
        assert "supported_formats" in data

    def test_get_category_suggestions(self, client, admin_headers):
        """Test getting category suggestions"""
        response = client.get(
            "/api/v1/ocr/categories/suggestions?vendor_name=Office%20Depot",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data

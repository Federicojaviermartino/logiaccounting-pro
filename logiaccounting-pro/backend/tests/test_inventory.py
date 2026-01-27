"""
Inventory endpoint tests
"""
import pytest


class TestMaterials:
    """Materials CRUD tests"""

    def test_get_materials_as_admin(self, client, admin_headers):
        """Test getting materials list as admin"""
        response = client.get("/api/v1/inventory/materials", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "materials" in data

    def test_get_materials_as_supplier(self, client, supplier_headers):
        """Test getting materials list as supplier"""
        response = client.get("/api/v1/inventory/materials", headers=supplier_headers)
        assert response.status_code == 200

    def test_get_materials_as_client_forbidden(self, client, client_headers):
        """Test client cannot access inventory"""
        response = client.get("/api/v1/inventory/materials", headers=client_headers)
        assert response.status_code == 403

    def test_get_materials_unauthenticated(self, client):
        """Test unauthenticated access denied"""
        response = client.get("/api/v1/inventory/materials")
        assert response.status_code == 401

    def test_create_material(self, client, admin_headers, sample_material):
        """Test creating a new material"""
        response = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["material"]["name"] == sample_material["name"]
        assert "id" in data["material"]

    def test_create_material_missing_name(self, client, admin_headers):
        """Test creating material without name fails"""
        response = client.post(
            "/api/v1/inventory/materials",
            json={"quantity": 100},
            headers=admin_headers
        )
        assert response.status_code == 422

    def test_update_material(self, client, admin_headers, sample_material):
        """Test updating a material"""
        # First create
        create_res = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        material_id = create_res.json()["material"]["id"]

        # Then update
        response = client.put(
            f"/api/v1/inventory/materials/{material_id}",
            json={"name": "Updated Material", "quantity": 200},
            headers=admin_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Material"
        assert response.json()["quantity"] == 200

    def test_delete_material(self, client, admin_headers, sample_material):
        """Test deleting a material"""
        # First create
        create_res = client.post(
            "/api/v1/inventory/materials",
            json=sample_material,
            headers=admin_headers
        )
        material_id = create_res.json()["material"]["id"]

        # Then delete
        response = client.delete(
            f"/api/v1/inventory/materials/{material_id}",
            headers=admin_headers
        )
        assert response.status_code == 200


class TestCategories:
    """Categories tests"""

    def test_get_categories(self, client, admin_headers):
        """Test getting categories"""
        response = client.get("/api/v1/inventory/categories", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data


class TestLocations:
    """Locations tests"""

    def test_get_locations(self, client, admin_headers):
        """Test getting locations"""
        response = client.get("/api/v1/inventory/locations", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "locations" in data

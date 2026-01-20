"""
In-memory data store for LogiAccounting Pro
Ready for PostgreSQL/SQLAlchemy migration
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__truncate_error=False)

class BaseStore:
    """Base class for data stores"""
    
    def __init__(self):
        self._data: List[Dict[str, Any]] = []
    
    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        results = self._data.copy()
        if filters:
            for key, value in filters.items():
                if value is not None:
                    results = [item for item in results if item.get(key) == value]
        return results
    
    def find_by_id(self, item_id: str) -> Optional[Dict]:
        return next((item for item in self._data if item["id"] == item_id), None)
    
    def create(self, data: Dict) -> Dict:
        item = {
            "id": str(uuid4()),
            **data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        self._data.append(item)
        return item
    
    def update(self, item_id: str, data: Dict) -> Optional[Dict]:
        for i, item in enumerate(self._data):
            if item["id"] == item_id:
                self._data[i] = {**item, **data, "updated_at": datetime.utcnow().isoformat()}
                return self._data[i]
        return None
    
    def delete(self, item_id: str) -> bool:
        for i, item in enumerate(self._data):
            if item["id"] == item_id:
                self._data.pop(i)
                return True
        return False


class UserStore(BaseStore):
    """User data store with password handling"""
    
    def find_by_email(self, email: str) -> Optional[Dict]:
        return next((u for u in self._data if u["email"] == email), None)
    
    def find_all_safe(self) -> List[Dict]:
        return [{k: v for k, v in u.items() if k != "password"} for u in self._data]
    
    def create(self, data: Dict) -> Dict:
        user = super().create({
            **data,
            "status": data.get("status", "active")
        })
        return {k: v for k, v in user.items() if k != "password"}
    
    def update_password(self, user_id: str, hashed_password: str) -> bool:
        for user in self._data:
            if user["id"] == user_id:
                user["password"] = hashed_password
                user["updated_at"] = datetime.utcnow().isoformat()
                return True
        return False


class MaterialStore(BaseStore):
    """Material/inventory store with advanced filtering"""
    
    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        results = self._data.copy()
        if filters:
            if filters.get("category_id"):
                results = [m for m in results if m.get("category_id") == filters["category_id"]]
            if filters.get("location_id"):
                results = [m for m in results if m.get("location_id") == filters["location_id"]]
            if filters.get("state"):
                results = [m for m in results if m.get("state") == filters["state"]]
            if filters.get("low_stock"):
                results = [m for m in results if m["quantity"] <= m.get("min_stock", 0)]
            if filters.get("search"):
                search = filters["search"].lower()
                results = [m for m in results if search in m["name"].lower() or search in m.get("reference", "").lower()]
        return results
    
    def find_by_reference(self, reference: str) -> Optional[Dict]:
        return next((m for m in self._data if m.get("reference") == reference), None)
    
    def update_quantity(self, material_id: str, delta: float) -> Optional[Dict]:
        for m in self._data:
            if m["id"] == material_id:
                m["quantity"] += delta
                m["updated_at"] = datetime.utcnow().isoformat()
                return m
        return None


class PaymentStore(BaseStore):
    """Payment store with overdue detection"""
    
    def find_all(self, filters: Optional[Dict] = None) -> List[Dict]:
        results = sorted(self._data, key=lambda x: x.get("due_date", ""), reverse=False)
        now = datetime.utcnow()
        
        for p in results:
            if p["status"] != "paid":
                try:
                    due_date = datetime.fromisoformat(p["due_date"].replace("Z", ""))
                    if due_date < now:
                        p["status"] = "overdue"
                except (ValueError, KeyError):
                    pass
        
        if filters:
            if filters.get("status"):
                results = [p for p in results if p["status"] == filters["status"]]
            if filters.get("type"):
                results = [p for p in results if p["type"] == filters["type"]]
            if filters.get("supplier_id"):
                results = [p for p in results if p.get("supplier_id") == filters["supplier_id"]]
            if filters.get("client_id"):
                results = [p for p in results if p.get("client_id") == filters["client_id"]]
        
        return results
    
    def mark_as_paid(self, payment_id: str, paid_date: Optional[str] = None) -> Optional[Dict]:
        for p in self._data:
            if p["id"] == payment_id:
                p["status"] = "paid"
                p["paid_date"] = paid_date or datetime.utcnow().isoformat()
                p["updated_at"] = datetime.utcnow().isoformat()
                return p
        return None


class NotificationStore(BaseStore):
    """Notification store with user/role filtering"""
    
    def find_by_user(self, user_id: str, user_role: str) -> List[Dict]:
        return sorted(
            [n for n in self._data if n.get("user_id") == user_id or n.get("target_role") == user_role],
            key=lambda x: x["created_at"],
            reverse=True
        )
    
    def mark_as_read(self, notif_id: str) -> bool:
        for n in self._data:
            if n["id"] == notif_id:
                n["read"] = True
                return True
        return False
    
    def mark_all_as_read(self, user_id: str, user_role: str) -> bool:
        for n in self._data:
            if n.get("user_id") == user_id or n.get("target_role") == user_role:
                n["read"] = True
        return True
    
    def get_unread_count(self, user_id: str, user_role: str) -> int:
        return len([n for n in self._data 
                   if (n.get("user_id") == user_id or n.get("target_role") == user_role) and not n.get("read")])


class Database:
    """Main database container"""

    def __init__(self):
        self.users = UserStore()
        self.categories = BaseStore()
        self.locations = BaseStore()
        self.materials = MaterialStore()
        self.projects = BaseStore()
        self.movements = BaseStore()
        self.transactions = BaseStore()
        self.payments = PaymentStore()
        self.notifications = NotificationStore()

        # SSO stores (Phase 12)
        from app.models.sso_store import (
            SSOConnectionStore, SSOSessionStore,
            UserExternalIdentityStore, SCIMSyncLogStore
        )
        self.sso_connections = SSOConnectionStore()
        self.sso_sessions = SSOSessionStore()
        self.external_identities = UserExternalIdentityStore()
        self.scim_logs = SCIMSyncLogStore()


# Global database instance
db = Database()


def init_database():
    """Initialize database with demo data"""
    
    # Demo users
    db.users.create({
        "email": "admin@logiaccounting.demo",
        "password": pwd_context.hash("Demo2024!Admin"),
        "first_name": "System",
        "last_name": "Administrator",
        "role": "admin",
        "company_name": "LogiAccounting Inc.",
        "phone": "+1 555 000 0001"
    })
    
    db.users.create({
        "email": "client@logiaccounting.demo",
        "password": pwd_context.hash("Demo2024!Client"),
        "first_name": "John",
        "last_name": "Client",
        "role": "client",
        "company_name": "Client Corp.",
        "phone": "+1 555 000 0002"
    })
    
    db.users.create({
        "email": "supplier@logiaccounting.demo",
        "password": pwd_context.hash("Demo2024!Supplier"),
        "first_name": "Jane",
        "last_name": "Supplier",
        "role": "supplier",
        "company_name": "Supply Co.",
        "phone": "+1 555 000 0003"
    })
    
    # Categories
    categories = [
        {"name": "Raw Materials", "type": "material"},
        {"name": "Finished Goods", "type": "material"},
        {"name": "Office Supplies", "type": "material"},
        {"name": "Equipment", "type": "material"},
        {"name": "Sales Revenue", "type": "income"},
        {"name": "Service Income", "type": "income"},
        {"name": "Operating Expenses", "type": "expense"},
        {"name": "Material Costs", "type": "expense"},
        {"name": "Labor Costs", "type": "expense"},
        {"name": "Utilities", "type": "expense"},
    ]
    for cat in categories:
        db.categories.create(cat)
    
    # Locations
    locations = [
        {"name": "Main Warehouse", "code": "WH-001", "address": "123 Industrial Ave"},
        {"name": "Secondary Warehouse", "code": "WH-002", "address": "456 Storage Blvd"},
        {"name": "Office Storage", "code": "OF-001", "address": "789 Corporate Dr"},
    ]
    for loc in locations:
        db.locations.create(loc)
    
    # Sample materials
    materials = [
        {"reference": "RM-001", "name": "Steel Sheets", "category_id": db.categories._data[0]["id"], 
         "location_id": db.locations._data[0]["id"], "quantity": 500, "min_stock": 100, "unit": "sheets", "unit_cost": 45.00, "state": "available"},
        {"reference": "RM-002", "name": "Aluminum Bars", "category_id": db.categories._data[0]["id"],
         "location_id": db.locations._data[0]["id"], "quantity": 250, "min_stock": 50, "unit": "bars", "unit_cost": 32.50, "state": "available"},
        {"reference": "FG-001", "name": "Assembled Module A", "category_id": db.categories._data[1]["id"],
         "location_id": db.locations._data[1]["id"], "quantity": 75, "min_stock": 20, "unit": "units", "unit_cost": 150.00, "state": "available"},
    ]
    for mat in materials:
        db.materials.create(mat)
    
    # Sample project
    db.projects.create({
        "code": "PRJ-2024-001",
        "name": "Warehouse Automation",
        "client": "TechCorp Industries",
        "client_id": db.users._data[1]["id"],
        "description": "Automated inventory management system",
        "budget": 150000,
        "status": "active",
        "start_date": "2024-01-15"
    })
    
    print("Database initialized with demo data")
    print(f"Users: {len(db.users._data)}, Categories: {len(db.categories._data)}, Locations: {len(db.locations._data)}")

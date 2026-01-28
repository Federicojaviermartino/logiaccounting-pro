"""
Data Backup and Restore Service
"""

import json
import gzip
import base64
from datetime import datetime
from typing import List, Dict, Optional
from app.models.store import db
from app.utils.datetime_utils import utc_now
from app.utils.activity_logger import activity_logger


class BackupService:
    """Manages data backup and restore operations"""

    _instance = None
    _backups: Dict[str, dict] = {}
    _counter = 0

    ENTITIES = ['materials', 'transactions', 'payments', 'projects', 'categories', 'locations']

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._backups = {}
            cls._counter = 0
        return cls._instance

    def create_backup(
        self,
        user_id: str,
        user_email: str,
        entities: Optional[List[str]] = None,
        include_users: bool = False
    ) -> dict:
        """Create a backup of specified entities"""
        self._counter += 1
        backup_id = f"BKP-{self._counter:06d}"

        entities_to_backup = entities or self.ENTITIES

        backup_data = {
            "version": "1.0",
            "created_at": utc_now().isoformat(),
            "created_by": user_email,
            "entities": {}
        }

        for entity in entities_to_backup:
            if entity == 'materials':
                backup_data["entities"]["materials"] = db.materials.find_all()
            elif entity == 'transactions':
                backup_data["entities"]["transactions"] = db.transactions.find_all()
            elif entity == 'payments':
                backup_data["entities"]["payments"] = db.payments.find_all()
            elif entity == 'projects':
                backup_data["entities"]["projects"] = db.projects.find_all()
            elif entity == 'categories':
                backup_data["entities"]["categories"] = db.categories.find_all()
            elif entity == 'locations':
                backup_data["entities"]["locations"] = db.locations.find_all()

        if include_users:
            users = db.users.find_all()
            backup_data["entities"]["users"] = [
                {k: v for k, v in u.items() if k != 'password'}
                for u in users
            ]

        json_data = json.dumps(backup_data)
        compressed = gzip.compress(json_data.encode())
        encoded = base64.b64encode(compressed).decode()

        backup_info = {
            "id": backup_id,
            "created_at": backup_data["created_at"],
            "created_by": user_email,
            "user_id": user_id,
            "entities": entities_to_backup,
            "include_users": include_users,
            "size_bytes": len(compressed),
            "record_counts": {
                entity: len(backup_data["entities"].get(entity, []))
                for entity in entities_to_backup
            }
        }

        self._backups[backup_id] = {**backup_info, "data": encoded}

        activity_logger.log(
            user_id=user_id,
            user_email=user_email,
            user_role="admin",
            action="CREATE",
            entity_type="backup",
            entity_id=backup_id,
            details={"entities": entities_to_backup}
        )

        return backup_info

    def get_backup_data(self, backup_id: str) -> Optional[str]:
        """Get the compressed backup data"""
        backup = self._backups.get(backup_id)
        return backup.get("data") if backup else None

    def list_backups(self, user_id: Optional[str] = None) -> List[dict]:
        """List all backups"""
        backups = []
        for bid, backup in self._backups.items():
            info = {k: v for k, v in backup.items() if k != 'data'}
            if user_id is None or backup.get("user_id") == user_id:
                backups.append(info)
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        if backup_id in self._backups:
            del self._backups[backup_id]
            return True
        return False

    def restore_backup(
        self,
        backup_data: str,
        user_id: str,
        user_email: str,
        entities: Optional[List[str]] = None,
        mode: str = "merge"
    ) -> dict:
        """Restore data from a backup"""
        try:
            compressed = base64.b64decode(backup_data)
            json_data = gzip.decompress(compressed).decode()
            data = json.loads(json_data)

            entities_to_restore = entities or list(data["entities"].keys())
            results = {"restored": {}, "errors": []}

            for entity in entities_to_restore:
                if entity not in data["entities"]:
                    results["errors"].append(f"Entity {entity} not found")
                    continue

                records = data["entities"][entity]
                restored_count = 0

                store = getattr(db, entity, None)
                if not store:
                    results["errors"].append(f"Unknown entity: {entity}")
                    continue

                if mode == "replace":
                    store._data = {}

                for record in records:
                    try:
                        if mode == "merge":
                            existing = store.find_by_id(record.get("id"))
                            if existing:
                                store.update(record["id"], record)
                            else:
                                store._data[record["id"]] = record
                        else:
                            store._data[record["id"]] = record
                        restored_count += 1
                    except Exception as e:
                        results["errors"].append(f"Error restoring {entity}: {str(e)}")

                results["restored"][entity] = restored_count

            activity_logger.log(
                user_id=user_id,
                user_email=user_email,
                user_role="admin",
                action="UPDATE",
                entity_type="backup",
                details={"mode": mode, "results": results}
            )

            return results

        except Exception as e:
            return {"error": str(e), "restored": {}, "errors": [str(e)]}


backup_service = BackupService()

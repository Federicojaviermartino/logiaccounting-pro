"""
Bank Reconciliation Service
Match bank statements with system transactions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app.models.store import db
from app.utils.datetime_utils import utc_now


class ReconciliationService:
    """Manages bank statement reconciliation"""

    _instance = None
    _statements: Dict[str, dict] = {}
    _counter = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._statements = {}
            cls._counter = 0
        return cls._instance

    def import_statement(
        self,
        bank_name: str,
        account_number: str,
        period_start: str,
        period_end: str,
        entries: List[dict],
        imported_by: str
    ) -> dict:
        """Import a bank statement"""
        self._counter += 1
        statement_id = f"STMT-{self._counter:04d}"

        # Process entries
        processed_entries = []
        for i, entry in enumerate(entries):
            processed_entries.append({
                "entry_id": f"E{i+1:04d}",
                "date": entry.get("date"),
                "description": entry.get("description", ""),
                "reference": entry.get("reference", ""),
                "amount": float(entry.get("amount", 0)),
                "balance": float(entry.get("balance", 0)) if entry.get("balance") else None,
                "matched": False,
                "matched_txn_id": None,
                "match_score": None
            })

        statement = {
            "id": statement_id,
            "bank_name": bank_name,
            "account_number": account_number[-4:] if len(account_number) > 4 else account_number,
            "period_start": period_start,
            "period_end": period_end,
            "entries": processed_entries,
            "entry_count": len(processed_entries),
            "total_credits": sum(e["amount"] for e in processed_entries if e["amount"] > 0),
            "total_debits": sum(e["amount"] for e in processed_entries if e["amount"] < 0),
            "matched_count": 0,
            "unmatched_count": len(processed_entries),
            "reconciled": False,
            "imported_by": imported_by,
            "imported_at": utc_now().isoformat()
        }

        self._statements[statement_id] = statement
        return statement

    def auto_match(self, statement_id: str, tolerance_percent: float = 5, tolerance_days: int = 3) -> dict:
        """Run auto-matching algorithm"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}

        transactions = db.transactions.find_all()

        matches = []
        for entry in statement["entries"]:
            if entry["matched"]:
                continue

            best_match = None
            best_score = 0

            for txn in transactions:
                if txn.get("reconciled"):
                    continue

                score = self._calculate_match_score(entry, txn, tolerance_percent, tolerance_days)

                if score > best_score and score >= 50:
                    best_score = score
                    best_match = txn

            if best_match and best_score >= 80:
                # Auto-match
                entry["matched"] = True
                entry["matched_txn_id"] = best_match["id"]
                entry["match_score"] = best_score
                matches.append({
                    "entry_id": entry["entry_id"],
                    "txn_id": best_match["id"],
                    "score": best_score,
                    "auto": True
                })
            elif best_match and best_score >= 50:
                # Suggest match
                entry["suggested_txn_id"] = best_match["id"]
                entry["match_score"] = best_score
                matches.append({
                    "entry_id": entry["entry_id"],
                    "txn_id": best_match["id"],
                    "score": best_score,
                    "auto": False,
                    "suggested": True
                })

        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])

        return {
            "statement_id": statement_id,
            "matches": matches,
            "auto_matched": len([m for m in matches if m.get("auto")]),
            "suggested": len([m for m in matches if m.get("suggested")]),
            "unmatched": statement["unmatched_count"]
        }

    def _calculate_match_score(
        self,
        entry: dict,
        txn: dict,
        tolerance_percent: float,
        tolerance_days: int
    ) -> int:
        """Calculate match score between bank entry and transaction"""
        score = 0

        # Amount matching (40 points max)
        entry_amount = abs(entry["amount"])
        txn_amount = abs(txn.get("amount", 0))

        if entry_amount == txn_amount:
            score += 40
        elif txn_amount > 0:
            diff_percent = abs(entry_amount - txn_amount) / txn_amount * 100
            if diff_percent <= tolerance_percent:
                score += int(40 - diff_percent * 3)

        # Date matching (30 points max)
        try:
            entry_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            txn_date = datetime.strptime(txn.get("date", ""), "%Y-%m-%d").date()

            day_diff = abs((entry_date - txn_date).days)

            if day_diff == 0:
                score += 30
            elif day_diff <= tolerance_days:
                score += int(30 - day_diff * 5)
        except (ValueError, TypeError):
            pass

        # Reference matching (20 points)
        entry_ref = entry.get("reference", "").lower()
        txn_ref = txn.get("invoice_number", "").lower() or txn.get("reference", "").lower()

        if entry_ref and txn_ref and (entry_ref in txn_ref or txn_ref in entry_ref):
            score += 20

        # Description matching (10 points)
        entry_desc = entry.get("description", "").lower()
        txn_desc = txn.get("description", "").lower()

        if entry_desc and txn_desc:
            words_match = len(set(entry_desc.split()) & set(txn_desc.split()))
            if words_match >= 2:
                score += 10
            elif words_match == 1:
                score += 5

        return score

    def manual_match(self, statement_id: str, entry_id: str, txn_id: str) -> dict:
        """Manually match an entry to a transaction"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}

        entry = next((e for e in statement["entries"] if e["entry_id"] == entry_id), None)
        if not entry:
            return {"error": "Entry not found"}

        entry["matched"] = True
        entry["matched_txn_id"] = txn_id
        entry["match_score"] = 100  # Manual = 100%

        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])

        return {"success": True, "entry": entry}

    def unmatch(self, statement_id: str, entry_id: str) -> dict:
        """Unmatch an entry"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}

        entry = next((e for e in statement["entries"] if e["entry_id"] == entry_id), None)
        if not entry:
            return {"error": "Entry not found"}

        entry["matched"] = False
        entry["matched_txn_id"] = None
        entry["match_score"] = None

        # Update counts
        statement["matched_count"] = len([e for e in statement["entries"] if e["matched"]])
        statement["unmatched_count"] = len([e for e in statement["entries"] if not e["matched"]])

        return {"success": True}

    def complete_reconciliation(self, statement_id: str) -> dict:
        """Mark statement as reconciled"""
        statement = self._statements.get(statement_id)
        if not statement:
            return {"error": "Statement not found"}

        if statement["unmatched_count"] > 0:
            return {"error": f"{statement['unmatched_count']} entries still unmatched"}

        statement["reconciled"] = True
        statement["reconciled_at"] = utc_now().isoformat()

        # Mark transactions as reconciled
        for entry in statement["entries"]:
            if entry["matched_txn_id"]:
                txn = db.transactions.find_by_id(entry["matched_txn_id"])
                if txn:
                    db.transactions.update(entry["matched_txn_id"], {"reconciled": True})

        return {"success": True, "statement": statement}

    def get_statement(self, statement_id: str) -> Optional[dict]:
        """Get a specific statement"""
        return self._statements.get(statement_id)

    def list_statements(self) -> List[dict]:
        """List all statements"""
        return sorted(
            self._statements.values(),
            key=lambda s: s["imported_at"],
            reverse=True
        )

    def get_unmatched_transactions(self, period_start: str, period_end: str) -> List[dict]:
        """Get unreconciled transactions in a period"""
        transactions = db.transactions.find_all()
        return [
            t for t in transactions
            if not t.get("reconciled")
            and period_start <= t.get("date", "") <= period_end
        ]

    def delete_statement(self, statement_id: str) -> bool:
        """Delete a statement"""
        if statement_id in self._statements:
            del self._statements[statement_id]
            return True
        return False


reconciliation_service = ReconciliationService()

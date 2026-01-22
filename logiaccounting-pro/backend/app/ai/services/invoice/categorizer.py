"""
Invoice Categorizer
Categorize invoices and suggest GL accounts
"""

import logging
from typing import Optional, Dict, Any, List, Tuple

from ...config import get_ai_config, ModelTier
from ...models.scanned_invoice import ScannedInvoice
from ..llm_client import get_llm_client

logger = logging.getLogger(__name__)


# Category to GL account mapping
DEFAULT_GL_MAPPINGS = {
    'Office Supplies': '6100',
    'Software & Subscriptions': '6200',
    'Professional Services': '6300',
    'Travel & Entertainment': '6400',
    'Utilities': '6500',
    'Marketing & Advertising': '6600',
    'Equipment': '1500',
    'Inventory Purchase': '1200',
    'Shipping & Logistics': '6700',
    'Insurance': '6800',
    'Rent & Facilities': '6900',
    'Payroll & Benefits': '5000',
    'Other': '6999',
}

# Keywords for rule-based categorization
CATEGORY_KEYWORDS = {
    'Office Supplies': ['staples', 'paper', 'office depot', 'supplies', 'pens', 'folders'],
    'Software & Subscriptions': ['software', 'subscription', 'saas', 'license', 'cloud', 'aws', 'azure', 'google cloud'],
    'Professional Services': ['consulting', 'legal', 'accounting', 'advisory', 'professional'],
    'Travel & Entertainment': ['hotel', 'flight', 'uber', 'lyft', 'restaurant', 'meal', 'travel'],
    'Utilities': ['electric', 'water', 'gas', 'phone', 'internet', 'utility'],
    'Marketing & Advertising': ['advertising', 'marketing', 'google ads', 'facebook', 'promotion'],
    'Equipment': ['computer', 'laptop', 'monitor', 'equipment', 'hardware', 'furniture'],
    'Inventory Purchase': ['inventory', 'merchandise', 'goods', 'product', 'wholesale'],
    'Shipping & Logistics': ['fedex', 'ups', 'dhl', 'shipping', 'freight', 'logistics'],
    'Insurance': ['insurance', 'policy', 'premium', 'coverage'],
    'Rent & Facilities': ['rent', 'lease', 'facility', 'building', 'property'],
}


class InvoiceCategorizer:
    """Categorize invoices using rules and AI"""

    def __init__(self):
        self.config = get_ai_config()
        self.llm = get_llm_client()
        self.gl_mappings = DEFAULT_GL_MAPPINGS.copy()

    def _rule_based_categorize(
        self,
        text: str,
        vendor_name: Optional[str] = None,
    ) -> Tuple[Optional[str], float]:
        """Categorize using keyword rules"""
        text_lower = text.lower()
        if vendor_name:
            text_lower += ' ' + vendor_name.lower()

        scores = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[category] = score

        if not scores:
            return None, 0.0

        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        confidence = min(0.9, 0.3 + (max_score * 0.15))

        return best_category, confidence

    async def categorize(
        self,
        scan: ScannedInvoice,
        use_llm: bool = True,
    ) -> ScannedInvoice:
        """
        Categorize a scanned invoice

        Args:
            scan: ScannedInvoice to categorize
            use_llm: Whether to use LLM for categorization

        Returns:
            Updated ScannedInvoice with category
        """
        # Try rule-based first
        vendor_name = scan.extracted_data.get('vendor_name')
        text_to_analyze = (scan.ocr_text or '') + ' ' + str(scan.extracted_data)

        category, confidence = self._rule_based_categorize(text_to_analyze, vendor_name)

        # Use LLM if rules are not confident enough
        if use_llm and (not category or confidence < 0.7):
            try:
                llm_category, llm_confidence = await self._llm_categorize(
                    scan.ocr_text or '',
                    scan.extracted_data,
                    scan.tenant_id,
                )
                if llm_confidence > confidence:
                    category = llm_category
                    confidence = llm_confidence
            except Exception as e:
                logger.warning(f"LLM categorization failed: {e}")

        # Default to 'Other' if no category found
        if not category:
            category = 'Other'
            confidence = 0.5

        # Update scan
        scan.category = category
        scan.category_confidence = confidence
        scan.suggested_gl_account = self.gl_mappings.get(category, '6999')

        scan.save()
        return scan

    async def _llm_categorize(
        self,
        ocr_text: str,
        extracted_data: Dict[str, Any],
        tenant_id: str,
    ) -> Tuple[str, float]:
        """Categorize using LLM"""
        categories_list = '\n'.join(f'- {cat}' for cat in ScannedInvoice.CATEGORIES)

        prompt = f"""Categorize this invoice into one of the following categories:

{categories_list}

Invoice information:
Vendor: {extracted_data.get('vendor_name', 'Unknown')}
Amount: {extracted_data.get('total_amount', 'Unknown')}
Description: {extracted_data.get('line_items', [])}

OCR Text excerpt:
{ocr_text[:1000]}

Respond with JSON:
{{"category": "category name", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

        result = await self.llm.extract_json(
            prompt=prompt,
            tier=ModelTier.FAST,
            tenant_id=tenant_id,
            feature='invoice_categorization',
        )

        category = result.get('category', 'Other')
        confidence = float(result.get('confidence', 0.5))

        # Validate category
        if category not in ScannedInvoice.CATEGORIES:
            category = 'Other'
            confidence = 0.5

        return category, confidence

    async def suggest_cost_center(
        self,
        scan: ScannedInvoice,
        available_cost_centers: List[Dict[str, str]],
    ) -> Optional[str]:
        """
        Suggest appropriate cost center for invoice

        Args:
            scan: ScannedInvoice
            available_cost_centers: List of {"id": "...", "name": "..."}

        Returns:
            Suggested cost center ID
        """
        if not available_cost_centers:
            return None

        # Simple matching based on category
        category = scan.category or 'Other'

        # Default mappings
        category_to_cost_center = {
            'Marketing & Advertising': 'marketing',
            'Professional Services': 'professional',
            'Software & Subscriptions': 'technology',
            'Equipment': 'operations',
            'Rent & Facilities': 'facilities',
        }

        suggested_type = category_to_cost_center.get(category, 'general')

        # Find matching cost center
        for cc in available_cost_centers:
            cc_name = cc.get('name', '').lower()
            if suggested_type in cc_name:
                return cc.get('id')

        # Return first available if no match
        return available_cost_centers[0].get('id') if available_cost_centers else None

    def update_gl_mapping(self, category: str, gl_account: str):
        """Update GL account mapping for category"""
        if category in ScannedInvoice.CATEGORIES:
            self.gl_mappings[category] = gl_account

"""
Document OCR Service - Phase 13
Tesseract-based OCR with PDF support
"""

from typing import Optional, Dict, Any, List, Tuple
import os
import logging
import tempfile
import re
from io import BytesIO

logger = logging.getLogger(__name__)


class DocumentOCRService:
    """OCR service for document text extraction"""

    SUPPORTED_FORMATS = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'tif', 'webp', 'bmp']

    def __init__(self):
        self._tesseract_available = None
        self._pytesseract = None
        self._pil = None
        self._pdf2image = None
        self._fitz = None

    @property
    def tesseract_available(self) -> bool:
        """Check if Tesseract is available"""
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
                self._pytesseract = pytesseract
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available

    @property
    def pil(self):
        """Lazy load PIL"""
        if self._pil is None:
            try:
                from PIL import Image
                self._pil = Image
            except ImportError:
                logger.warning("PIL not available")
        return self._pil

    @property
    def pdf2image(self):
        """Lazy load pdf2image"""
        if self._pdf2image is None:
            try:
                import pdf2image
                self._pdf2image = pdf2image
            except ImportError:
                logger.warning("pdf2image not available")
        return self._pdf2image

    @property
    def fitz(self):
        """Lazy load PyMuPDF (fitz)"""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                logger.warning("PyMuPDF not available")
        return self._fitz

    def extract_text(
        self,
        file_content: bytes,
        filename: str,
        language: str = 'eng+spa',
        dpi: int = 300,
        preprocess: bool = True
    ) -> Dict[str, Any]:
        """
        Extract text from document

        Args:
            file_content: File content bytes
            filename: Original filename
            language: Tesseract language codes
            dpi: DPI for PDF conversion
            preprocess: Apply image preprocessing

        Returns:
            Dict with text, confidence, and page data
        """
        ext = os.path.splitext(filename)[1].lower().lstrip('.')

        if ext not in self.SUPPORTED_FORMATS:
            return {
                'success': False,
                'error': f'Unsupported format: {ext}'
            }

        if not self.tesseract_available:
            return {
                'success': False,
                'error': 'Tesseract OCR not available'
            }

        try:
            if ext == 'pdf':
                return self._extract_from_pdf(file_content, language, dpi, preprocess)
            else:
                return self._extract_from_image(file_content, language, preprocess)

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_from_image(
        self,
        file_content: bytes,
        language: str,
        preprocess: bool
    ) -> Dict[str, Any]:
        """Extract text from image file"""
        if not self.pil:
            return {'success': False, 'error': 'PIL not available'}

        image = self.pil.open(BytesIO(file_content))

        if preprocess:
            image = self._preprocess_image(image)

        # Get detailed OCR data
        ocr_data = self._pytesseract.image_to_data(
            image,
            lang=language,
            output_type=self._pytesseract.Output.DICT
        )

        # Extract text and calculate confidence
        text = self._pytesseract.image_to_string(image, lang=language)
        confidences = [c for c in ocr_data['conf'] if c > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        # Extract word positions for searchable PDF generation
        words = []
        for i, word in enumerate(ocr_data['text']):
            if word.strip():
                words.append({
                    'text': word,
                    'x': ocr_data['left'][i],
                    'y': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i],
                    'confidence': ocr_data['conf'][i],
                })

        return {
            'success': True,
            'text': text.strip(),
            'confidence': avg_confidence,
            'pages': [
                {
                    'page_number': 1,
                    'text': text.strip(),
                    'words': words,
                    'confidence': avg_confidence,
                }
            ],
            'word_count': len(text.split()),
        }

    def _extract_from_pdf(
        self,
        file_content: bytes,
        language: str,
        dpi: int,
        preprocess: bool
    ) -> Dict[str, Any]:
        """Extract text from PDF file"""
        # First try to extract embedded text
        embedded_text = self._extract_embedded_text(file_content)

        if embedded_text and len(embedded_text.strip()) > 100:
            # PDF has embedded text, use it
            return {
                'success': True,
                'text': embedded_text,
                'confidence': 100.0,
                'pages': [
                    {
                        'page_number': i + 1,
                        'text': page_text,
                        'confidence': 100.0,
                    }
                    for i, page_text in enumerate(embedded_text.split('\f'))
                ],
                'word_count': len(embedded_text.split()),
                'method': 'embedded'
            }

        # Fall back to OCR
        if not self.pdf2image:
            return {'success': False, 'error': 'pdf2image not available for OCR'}

        if not self.pil:
            return {'success': False, 'error': 'PIL not available for OCR'}

        # Convert PDF pages to images
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            images = self.pdf2image.convert_from_path(
                tmp_path,
                dpi=dpi,
                fmt='png'
            )

            all_text = []
            all_confidences = []
            pages = []

            for i, image in enumerate(images):
                if preprocess:
                    image = self._preprocess_image(image)

                text = self._pytesseract.image_to_string(image, lang=language)
                ocr_data = self._pytesseract.image_to_data(
                    image,
                    lang=language,
                    output_type=self._pytesseract.Output.DICT
                )

                confidences = [c for c in ocr_data['conf'] if c > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                all_text.append(text)
                all_confidences.extend(confidences)

                pages.append({
                    'page_number': i + 1,
                    'text': text.strip(),
                    'confidence': avg_confidence,
                })

            full_text = '\n\n'.join(all_text)
            overall_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

            return {
                'success': True,
                'text': full_text.strip(),
                'confidence': overall_confidence,
                'pages': pages,
                'word_count': len(full_text.split()),
                'method': 'ocr'
            }

        finally:
            os.unlink(tmp_path)

    def _extract_embedded_text(self, file_content: bytes) -> Optional[str]:
        """Extract embedded text from PDF using PyMuPDF"""
        if not self.fitz:
            return None

        try:
            doc = self.fitz.open(stream=file_content, filetype='pdf')
            text_parts = []

            for page in doc:
                text = page.get_text()
                text_parts.append(text)

            doc.close()
            return '\f'.join(text_parts)

        except Exception as e:
            logger.warning(f"Failed to extract embedded PDF text: {e}")
            return None

    def _preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        if not self.pil:
            return image

        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Apply simple threshold for better text recognition
        try:
            import numpy as np

            img_array = np.array(image)

            # Adaptive thresholding simulation
            mean_val = img_array.mean()
            threshold = mean_val * 0.9

            img_array = np.where(img_array > threshold, 255, 0).astype(np.uint8)

            image = self.pil.fromarray(img_array)

        except ImportError:
            pass

        return image

    def detect_document_type(self, text: str) -> Tuple[str, float]:
        """
        Detect document type from OCR text

        Returns:
            Tuple of (document_type, confidence)
        """
        text_lower = text.lower()

        patterns = {
            'invoice': [
                r'\b(invoice|factura|rechnung|bill)\b',
                r'\b(total|subtotal|amount due)\b',
                r'\b(qty|quantity|cantidad)\b',
                r'\b(unit price|precio|price)\b',
            ],
            'receipt': [
                r'\b(receipt|recibo|quittung)\b',
                r'\b(cash|change|paid)\b',
                r'\b(thank you|gracias)\b',
            ],
            'contract': [
                r'\b(contract|agreement|contrato)\b',
                r'\b(parties|party|parte)\b',
                r'\b(terms and conditions|terms)\b',
                r'\b(signature|firma|sign)\b',
            ],
            'statement': [
                r'\b(statement|estado de cuenta|bank statement)\b',
                r'\b(balance|saldo|opening balance|closing balance)\b',
                r'\b(deposits|withdrawals)\b',
            ],
            'id_document': [
                r'\b(passport|pasaporte|id card|identification)\b',
                r'\b(date of birth|dob|fecha de nacimiento)\b',
                r'\b(nationality|nacionalidad)\b',
            ],
            'certificate': [
                r'\b(certificate|certificado|diploma)\b',
                r'\b(certify|certified|certifica)\b',
                r'\b(awarded|granted)\b',
            ],
        }

        scores = {}

        for doc_type, type_patterns in patterns.items():
            matches = 0
            for pattern in type_patterns:
                if re.search(pattern, text_lower):
                    matches += 1
            scores[doc_type] = matches / len(type_patterns)

        if not scores:
            return ('other', 0.0)

        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        if confidence < 0.25:
            return ('other', confidence)

        return (best_type, confidence)

    def extract_key_values(self, text: str, document_type: str = None) -> Dict[str, Any]:
        """
        Extract common key-value pairs from OCR text

        Args:
            text: OCR extracted text
            document_type: Optional document type hint

        Returns:
            Dict of extracted values
        """
        extracted = {}

        # Date patterns
        date_patterns = [
            r'(?:date|fecha|datum)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['date'] = match.group(1)
                break

        # Amount patterns
        amount_patterns = [
            r'(?:total|amount|importe|monto)[:\s]*[\$\u20ac\u00a3]?\s*([0-9,]+\.?\d*)',
            r'[\$\u20ac\u00a3]\s*([0-9,]+\.?\d*)',
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    extracted['amount'] = float(amount_str)
                except ValueError:
                    pass
                break

        # Invoice/Reference number
        ref_patterns = [
            r'(?:invoice|factura|ref|reference|no|number)[#:\s]*([A-Z0-9-]+)',
            r'#\s*([A-Z0-9-]+)',
        ]

        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['reference'] = match.group(1)
                break

        # Tax ID / VAT
        tax_patterns = [
            r'(?:tax id|vat|nif|cif|rfc)[:\s]*([A-Z0-9-]+)',
            r'(?:fiscal|tax)[:\s]*([A-Z0-9-]+)',
        ]

        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted['tax_id'] = match.group(1)
                break

        # Email
        email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
        if email_match:
            extracted['email'] = email_match.group(1)

        # Phone
        phone_match = re.search(r'(?:tel|phone|telefono)[:\s]*([+\d\s()-]+)', text, re.IGNORECASE)
        if phone_match:
            extracted['phone'] = phone_match.group(1).strip()

        return extracted


# Global service instance
document_ocr_service = DocumentOCRService()

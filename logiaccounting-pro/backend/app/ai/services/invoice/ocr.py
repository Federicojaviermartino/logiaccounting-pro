"""
Invoice OCR Service
Extract text from invoice images using Tesseract
"""

import logging
import time
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import io

from ...config import get_ai_config

logger = logging.getLogger(__name__)


class InvoiceOCR:
    """OCR service for invoice images"""

    def __init__(self):
        self.config = get_ai_config()
        self._tesseract_available = None

    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        if self._tesseract_available is not None:
            return self._tesseract_available

        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            logger.warning("Tesseract not available")
            self._tesseract_available = False

        return self._tesseract_available

    def _preprocess_image(self, image_data: bytes) -> Any:
        """Preprocess image for better OCR results"""
        try:
            from PIL import Image, ImageEnhance, ImageFilter
        except ImportError:
            raise RuntimeError("Pillow not installed")

        # Open image
        image = Image.open(io.BytesIO(image_data))

        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Enhance contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Apply sharpening
        image = image.filter(ImageFilter.SHARPEN)

        # Apply threshold for binarization
        threshold = 150
        image = image.point(lambda p: 255 if p > threshold else 0)

        return image

    def extract_text(
        self,
        image_data: bytes,
        language: str = 'eng',
    ) -> Tuple[str, float]:
        """
        Extract text from image using OCR

        Args:
            image_data: Image file bytes
            language: OCR language code

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        if not self._check_tesseract():
            return self._fallback_extraction(image_data)

        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            return self._fallback_extraction(image_data)

        start_time = time.time()

        # Preprocess image
        processed_image = self._preprocess_image(image_data)

        # Configure Tesseract
        custom_config = r'--oem 3 --psm 6'

        # Extract text with confidence data
        data = pytesseract.image_to_data(
            processed_image,
            lang=language,
            config=custom_config,
            output_type=pytesseract.Output.DICT,
        )

        # Combine text and calculate confidence
        words = []
        confidences = []

        for i, word in enumerate(data['text']):
            if word.strip():
                words.append(word)
                conf = data['conf'][i]
                if conf > 0:
                    confidences.append(conf)

        text = ' '.join(words)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        confidence_score = avg_confidence / 100.0

        processing_time = time.time() - start_time
        logger.info(f"OCR completed in {processing_time:.2f}s, confidence: {confidence_score:.2f}")

        return text, confidence_score

    def _fallback_extraction(self, image_data: bytes) -> Tuple[str, float]:
        """Fallback when Tesseract is not available"""
        logger.warning("Using fallback OCR (placeholder)")
        return "", 0.0

    def extract_from_pdf(
        self,
        pdf_data: bytes,
        language: str = 'eng',
    ) -> Tuple[str, float]:
        """
        Extract text from PDF

        Args:
            pdf_data: PDF file bytes
            language: OCR language code

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            logger.warning("PyMuPDF not available for PDF processing")
            return "", 0.0

        doc = fitz.open(stream=pdf_data, filetype="pdf")
        all_text = []
        confidences = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Try to extract text directly first
            text = page.get_text()

            if text.strip():
                all_text.append(text)
                confidences.append(0.95)  # High confidence for direct text
            else:
                # Fall back to OCR for image-based pages
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")

                page_text, page_conf = self.extract_text(img_data, language)
                all_text.append(page_text)
                confidences.append(page_conf)

        combined_text = '\n'.join(all_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return combined_text, avg_confidence

    def detect_document_type(self, text: str) -> str:
        """
        Detect document type from extracted text

        Args:
            text: OCR extracted text

        Returns:
            Document type string
        """
        text_lower = text.lower()

        if any(kw in text_lower for kw in ['invoice', 'factura', 'bill to', 'invoice number']):
            return 'invoice'
        elif any(kw in text_lower for kw in ['receipt', 'recibo', 'payment received']):
            return 'receipt'
        elif any(kw in text_lower for kw in ['purchase order', 'p.o.', 'orden de compra']):
            return 'purchase_order'
        elif any(kw in text_lower for kw in ['quote', 'quotation', 'cotizacion', 'estimate']):
            return 'quote'
        elif any(kw in text_lower for kw in ['credit note', 'nota de credito']):
            return 'credit_note'
        else:
            return 'unknown'

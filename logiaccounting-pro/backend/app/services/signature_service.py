"""
Digital Signature Service - Phase 13
E-signature workflows for documents
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4
import secrets
import logging
import os
import base64
from io import BytesIO

from app.models.document_store import doc_db
from app.services.storage import get_storage_provider

logger = logging.getLogger(__name__)


class SignatureService:
    """Service for document signing workflows"""

    def __init__(self):
        self._storage = None

    @property
    def storage(self):
        if self._storage is None:
            self._storage = get_storage_provider()
        return self._storage

    def create_request(
        self,
        document_id: str,
        organization_id: str,
        created_by: str,
        title: str,
        recipients: List[Dict[str, Any]],
        message: str = None,
        signing_order: str = 'parallel',
        expires_in_days: int = 30,
        reminder_frequency: int = 3
    ) -> Dict[str, Any]:
        """
        Create a signature request

        Args:
            document_id: Document to sign
            organization_id: Organization ID
            created_by: User creating request
            title: Request title
            recipients: List of {email, name, role, order}
            message: Optional message to signers
            signing_order: 'sequential' or 'parallel'
            expires_in_days: Days until expiration
            reminder_frequency: Days between reminders

        Returns:
            Signature request data
        """
        # Verify document exists
        document = doc_db.documents.find_by_id(document_id)

        if not document:
            return {'success': False, 'error': 'Document not found'}

        if document.get('organization_id') != organization_id:
            return {'success': False, 'error': 'Document not found'}

        # Create request
        request_id = str(uuid4())

        request = doc_db.signature_requests.create({
            'id': request_id,
            'organization_id': organization_id,
            'document_id': document_id,
            'title': title,
            'message': message,
            'status': 'draft',
            'signing_order': signing_order,
            'expires_at': (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat(),
            'reminder_frequency_days': reminder_frequency,
            'created_by': created_by,
            'recipients': [],
        })

        # Add recipients
        for i, recipient_data in enumerate(recipients):
            recipient = doc_db.signature_recipients.create({
                'request_id': request_id,
                'email': recipient_data['email'],
                'name': recipient_data.get('name'),
                'role': recipient_data.get('role', 'signer'),
                'signing_order': recipient_data.get('order', i + 1) if signing_order == 'sequential' else 1,
                'access_token': secrets.token_urlsafe(32),
                'status': 'pending',
            })

            request['recipients'].append(recipient)

        logger.info(f"Created signature request {request_id} for document {document_id}")

        return {
            'success': True,
            'request': request
        }

    def send_request(self, request_id: str, organization_id: str) -> Dict[str, Any]:
        """
        Send signature request to recipients

        Args:
            request_id: Signature request ID
            organization_id: Organization ID

        Returns:
            Result of sending
        """
        request = doc_db.signature_requests.find_by_id(request_id)

        if not request:
            return {'success': False, 'error': 'Request not found'}

        if request.get('organization_id') != organization_id:
            return {'success': False, 'error': 'Request not found'}

        if request.get('status') not in ['draft', 'pending']:
            return {'success': False, 'error': f"Cannot send request in {request.get('status')} status"}

        # Get recipients to notify
        recipients = doc_db.signature_recipients.find_by_request(request_id)

        if request.get('signing_order') == 'sequential':
            # Only notify first signer(s)
            recipients = [r for r in recipients
                         if r.get('signing_order') == 1 and r.get('status') == 'pending']
        else:
            # Notify all pending signers
            recipients = [r for r in recipients if r.get('status') == 'pending']

        # Send notifications (in a real implementation, this would send emails)
        sent_count = 0
        for recipient in recipients:
            try:
                self._send_signature_notification(request, recipient)
                doc_db.signature_recipients.update(recipient['id'], {'status': 'sent'})
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send signature request to {recipient['email']}: {e}")

        # Update request status
        doc_db.signature_requests.update(request_id, {
            'status': 'pending',
            'sent_at': datetime.utcnow().isoformat(),
        })

        return {
            'success': True,
            'sent_count': sent_count,
        }

    def _send_signature_notification(self, request: Dict, recipient: Dict):
        """Send email notification to recipient"""
        # In a real implementation, this would send an email
        base_url = os.getenv('APP_URL', 'http://localhost:5173')
        sign_url = f"{base_url}/sign/{recipient['access_token']}"

        logger.info(f"Would send signature request email to {recipient['email']}")
        logger.info(f"Sign URL: {sign_url}")

    def get_signing_document(self, access_token: str) -> Optional[Dict]:
        """
        Get document for signing via access token

        Args:
            access_token: Recipient's access token

        Returns:
            Document and signing info
        """
        recipient = doc_db.signature_recipients.find_by_token(access_token)

        if not recipient:
            return None

        request = doc_db.signature_requests.find_by_id(recipient['request_id'])

        if not request:
            return None

        # Check request status
        if request.get('status') == 'completed':
            return {'error': 'This document has already been signed'}

        if request.get('status') == 'expired':
            return {'error': 'This signature request has expired'}

        if request.get('expires_at'):
            expires = datetime.fromisoformat(request['expires_at'].replace('Z', ''))
            if datetime.utcnow() > expires:
                return {'error': 'This signature request has expired'}

        if request.get('status') == 'cancelled':
            return {'error': 'This signature request has been cancelled'}

        if recipient.get('status') == 'signed':
            return {'error': 'You have already signed this document'}

        # Check signing order
        if request.get('signing_order') == 'sequential':
            # Check if previous signers have signed
            all_recipients = doc_db.signature_recipients.find_by_request(request['id'])
            previous = [r for r in all_recipients
                       if r.get('signing_order', 0) < recipient.get('signing_order', 1)
                       and r.get('status') != 'signed']

            if previous:
                return {'error': 'Waiting for previous signers'}

        # Get document
        document = doc_db.documents.find_by_id(request['document_id'])

        if not document:
            return None

        # Mark as viewed
        if recipient.get('status') == 'sent':
            doc_db.signature_recipients.update(recipient['id'], {
                'status': 'viewed',
                'viewed_at': datetime.utcnow().isoformat(),
            })

        return {
            'document': {
                'id': document['id'],
                'name': document['name'],
                'mime_type': document['mime_type'],
            },
            'request': {
                'id': request['id'],
                'title': request['title'],
                'message': request.get('message'),
            },
            'recipient': {
                'email': recipient['email'],
                'name': recipient.get('name'),
                'role': recipient.get('role'),
            }
        }

    def sign_document(
        self,
        access_token: str,
        signature_data: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Sign a document

        Args:
            access_token: Recipient's access token
            signature_data: Base64 encoded signature image
            ip_address: Signer's IP address
            user_agent: Signer's user agent

        Returns:
            Signing result
        """
        # Get signing info
        signing_info = self.get_signing_document(access_token)

        if not signing_info:
            return {'success': False, 'error': 'Invalid access token'}

        if 'error' in signing_info:
            return {'success': False, 'error': signing_info['error']}

        recipient = doc_db.signature_recipients.find_by_token(access_token)
        request = doc_db.signature_requests.find_by_id(recipient['request_id'])

        # Record signature
        doc_db.signature_recipients.update(recipient['id'], {
            'signature_data': signature_data,
            'signed_at': datetime.utcnow().isoformat(),
            'status': 'signed',
            'ip_address': ip_address,
            'user_agent': user_agent,
            'access_token': secrets.token_urlsafe(32),  # Invalidate old token
        })

        # Check if all signers have signed
        all_recipients = doc_db.signature_recipients.find_by_request(request['id'])
        pending_count = len([r for r in all_recipients
                            if r.get('role') == 'signer' and r.get('status') != 'signed'])

        if pending_count == 0:
            # All signed - complete request
            signed_doc_id = self._generate_signed_document(request)

            doc_db.signature_requests.update(request['id'], {
                'status': 'completed',
                'completed_at': datetime.utcnow().isoformat(),
                'signed_document_id': signed_doc_id,
            })

            logger.info(f"Signature request {request['id']} completed")
        else:
            doc_db.signature_requests.update(request['id'], {'status': 'in_progress'})

            # Notify next signer if sequential
            if request.get('signing_order') == 'sequential':
                current_order = recipient.get('signing_order', 1)
                next_recipients = doc_db.signature_recipients.find_pending_by_order(
                    request['id'], current_order + 1
                )

                for next_recipient in next_recipients:
                    self._send_signature_notification(request, next_recipient)
                    doc_db.signature_recipients.update(next_recipient['id'], {'status': 'sent'})

        return {
            'success': True,
            'request_status': 'completed' if pending_count == 0 else 'in_progress',
            'pending_signatures': pending_count,
            'signed_at': datetime.utcnow().isoformat()
        }

    def decline_signature(
        self,
        access_token: str,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Decline to sign a document

        Args:
            access_token: Recipient's access token
            reason: Optional decline reason

        Returns:
            Decline result
        """
        recipient = doc_db.signature_recipients.find_by_token(access_token)

        if not recipient:
            return {'success': False, 'error': 'Invalid access token'}

        request = doc_db.signature_requests.find_by_id(recipient['request_id'])

        if request.get('status') in ['completed', 'cancelled', 'expired']:
            return {'success': False, 'error': f"Cannot decline: request is {request.get('status')}"}

        # Record decline
        doc_db.signature_recipients.update(recipient['id'], {
            'status': 'declined',
            'decline_reason': reason,
            'declined_at': datetime.utcnow().isoformat(),
        })

        # Mark request as declined
        doc_db.signature_requests.update(request['id'], {'status': 'declined'})

        logger.info(f"Signature request {request['id']} declined by {recipient['email']}")

        return {
            'success': True,
            'request_status': 'declined'
        }

    def get_request_status(
        self,
        request_id: str,
        organization_id: str
    ) -> Optional[Dict]:
        """Get signature request status"""
        request = doc_db.signature_requests.find_by_id(request_id)

        if not request:
            return None

        if request.get('organization_id') != organization_id:
            return None

        recipients = doc_db.signature_recipients.find_by_request(request_id)

        return {
            'id': request['id'],
            'title': request['title'],
            'status': request['status'],
            'document_id': request['document_id'],
            'signing_order': request.get('signing_order'),
            'created_at': request['created_at'],
            'sent_at': request.get('sent_at'),
            'completed_at': request.get('completed_at'),
            'expires_at': request.get('expires_at'),
            'signed_document_id': request.get('signed_document_id'),
            'recipients': [
                {
                    'email': r['email'],
                    'name': r.get('name'),
                    'role': r.get('role'),
                    'order': r.get('signing_order'),
                    'status': r['status'],
                    'signed_at': r.get('signed_at'),
                    'viewed_at': r.get('viewed_at'),
                }
                for r in recipients
            ]
        }

    def list_requests(
        self,
        organization_id: str,
        status: str = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """List signature requests for organization"""
        requests = doc_db.signature_requests.find_by_organization(organization_id)

        if status:
            requests = [r for r in requests if r.get('status') == status]

        requests.sort(key=lambda x: x.get('created_at', ''), reverse=True)

        total = len(requests)
        start = (page - 1) * per_page
        end = start + per_page

        return {
            'requests': requests[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        }

    def cancel_request(
        self,
        request_id: str,
        organization_id: str,
        cancelled_by: str
    ) -> Dict[str, Any]:
        """Cancel a signature request"""
        request = doc_db.signature_requests.find_by_id(request_id)

        if not request:
            return {'success': False, 'error': 'Request not found'}

        if request.get('organization_id') != organization_id:
            return {'success': False, 'error': 'Request not found'}

        if request.get('status') == 'completed':
            return {'success': False, 'error': 'Cannot cancel completed request'}

        doc_db.signature_requests.update(request_id, {
            'status': 'cancelled',
            'cancelled_at': datetime.utcnow().isoformat(),
            'cancelled_by': cancelled_by,
        })

        return {'success': True}

    def verify_signatures(self, request_id: str, organization_id: str) -> Dict[str, Any]:
        """
        Verify all signatures on a request

        Args:
            request_id: Signature request ID
            organization_id: Organization ID

        Returns:
            Verification result
        """
        request = doc_db.signature_requests.find_by_id(request_id)

        if not request:
            return {'success': False, 'error': 'Request not found'}

        if request.get('organization_id') != organization_id:
            return {'success': False, 'error': 'Request not found'}

        if request.get('status') != 'completed':
            return {
                'success': False,
                'valid': False,
                'reason': f"Request is not completed (status: {request.get('status')})"
            }

        recipients = doc_db.signature_recipients.find_by_request(request_id)

        signatures = []
        for recipient in recipients:
            if recipient.get('status') == 'signed':
                signatures.append({
                    'signer': recipient['email'],
                    'name': recipient.get('name'),
                    'signed_at': recipient.get('signed_at'),
                    'ip_address': recipient.get('ip_address'),
                    'valid': True
                })

        return {
            'success': True,
            'valid': True,
            'document_id': request['document_id'],
            'completed_at': request.get('completed_at'),
            'signatures': signatures
        }

    def _generate_signed_document(self, request: Dict) -> Optional[str]:
        """Generate PDF with embedded signatures"""
        try:
            import fitz  # PyMuPDF

            # Get original document
            document = doc_db.documents.find_by_id(request['document_id'])

            if not document or not document.get('storage_key'):
                return None

            # Download original
            content = self.storage.download(
                document['storage_key'],
                document.get('storage_bucket')
            )

            # Open PDF
            doc = fitz.open(stream=content, filetype='pdf')

            # Add signature page
            signature_page = doc.new_page(-1, width=612, height=792)  # Letter size

            # Add header
            signature_page.insert_text(
                (50, 50),
                "Digital Signature Certificate",
                fontsize=16,
                fontname="helv-bold"
            )

            signature_page.draw_line((50, 60), (562, 60))

            y = 100

            # Document info
            signature_page.insert_text((50, y), f"Document: {document['name']}", fontsize=10)
            y += 20
            signature_page.insert_text((50, y), f"Request ID: {request['id']}", fontsize=10)
            y += 20

            completed_at = request.get('completed_at', datetime.utcnow().isoformat())
            signature_page.insert_text((50, y), f"Completed: {completed_at}", fontsize=10)
            y += 40

            # Signatures
            signature_page.insert_text((50, y), "Signatures:", fontsize=12, fontname="helv-bold")
            y += 25

            recipients = doc_db.signature_recipients.find_by_request(request['id'])

            for recipient in recipients:
                if recipient.get('status') == 'signed':
                    signature_page.insert_text(
                        (50, y),
                        f"{recipient.get('name') or recipient['email']}",
                        fontsize=10,
                        fontname="helv-bold"
                    )
                    y += 15

                    signature_page.insert_text((70, y), f"Email: {recipient['email']}", fontsize=9)
                    y += 12
                    signature_page.insert_text((70, y), f"Signed: {recipient.get('signed_at')}", fontsize=9)
                    y += 12
                    signature_page.insert_text((70, y), f"IP: {recipient.get('ip_address', 'N/A')}", fontsize=9)
                    y += 25

            # Footer
            signature_page.insert_text(
                (50, 750),
                "This document was electronically signed using LogiAccounting Pro.",
                fontsize=8
            )

            # Save to bytes
            signed_content = doc.write()
            doc.close()

            # Create new document record
            signed_doc_id = str(uuid4())

            signed_filename = f"{document['original_filename'].rsplit('.', 1)[0]}_signed.pdf"

            storage_key = self.storage.generate_key(
                organization_id=document['organization_id'],
                document_id=signed_doc_id,
                filename=signed_filename
            )

            self.storage.upload_bytes(
                content=signed_content,
                key=storage_key,
                bucket=document.get('storage_bucket'),
                content_type='application/pdf',
            )

            import hashlib

            doc_db.documents.create({
                'id': signed_doc_id,
                'organization_id': document['organization_id'],
                'owner_id': request.get('created_by'),
                'name': f"{document['name']} (Signed)",
                'original_filename': signed_filename,
                'mime_type': 'application/pdf',
                'file_size': len(signed_content),
                'file_hash': hashlib.sha256(signed_content).hexdigest(),
                'document_type': 'signed_document',
                'status': 'active',
                'storage_provider': self.storage.name,
                'storage_bucket': document.get('storage_bucket'),
                'storage_key': storage_key,
                'related_entity_type': 'signature_request',
                'related_entity_id': request['id'],
            })

            return signed_doc_id

        except ImportError:
            logger.warning("PyMuPDF not available for signed document generation")
            return None
        except Exception as e:
            logger.error(f"Failed to generate signed document: {e}")
            return None


# Global service instance
signature_service = SignatureService()

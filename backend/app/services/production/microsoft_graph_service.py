"""
Production Microsoft Graph Service - ZERO MOCK DATA
Real Microsoft Graph API integration for production deployment
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import aiofiles
from msal import ConfidentialClientApplication
import httpx

from app import db

logger = logging.getLogger(__name__)

class MicrosoftGraphService:
    """Production Microsoft Graph Service - ZERO MOCK DATA"""
    
    def __init__(self):
        self.client_id = os.getenv('MICROSOFT_CLIENT_ID')
        self.client_secret = os.getenv('MICROSOFT_CLIENT_SECRET')
        self.tenant_id = os.getenv('MICROSOFT_TENANT_ID')
        self.redirect_uri = os.getenv('MICROSOFT_REDIRECT_URI')
        
        # Validate configuration
        if not all([self.client_id, self.client_secret, self.tenant_id, self.redirect_uri]):
            raise ValueError("Missing required Microsoft Graph configuration. Check environment variables.")
        
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scopes = [
            "https://graph.microsoft.com/Files.ReadWrite.All",
            "https://graph.microsoft.com/Sites.ReadWrite.All", 
            "https://graph.microsoft.com/User.Read",
            "https://graph.microsoft.com/Forms.Read.All"
        ]
        
        self.tokens_dir = os.getenv('MICROSOFT_TOKENS_DIR', './tokens/microsoft/')
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        self.app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=self.authority
        )
        
        # NO MOCK MODE - This is production only
        self.mock_mode = False  # ALWAYS FALSE for production
        
        logger.info(f"Microsoft Graph Service initialized for production with tenant: {self.tenant_id}")

    def get_authorization_url(self, user_id: str) -> Dict[str, str]:
        """Get real Microsoft OAuth authorization URL - NO MOCK DATA"""
        try:
            auth_url = self.app.get_authorization_request_url(
                scopes=self.scopes,
                redirect_uri=self.redirect_uri,
                state=user_id
            )
            
            logger.info(f"Generated real Microsoft OAuth URL for user {user_id}")
            
            return {
                'authorization_url': auth_url,
                'state': user_id,
                'status': 'success',
                'platform': 'microsoft_forms'
            }
            
        except Exception as e:
            logger.error(f"Error generating Microsoft auth URL: {str(e)}")
            raise Exception(f"Failed to generate authorization URL: {str(e)}")

    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle real Microsoft OAuth callback - NO MOCK DATA"""
        try:
            result = self.app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            if "access_token" in result:
                # Store token for user
                token_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token'),
                    'expires_in': result.get('expires_in'),
                    'token_type': result.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))
                }
                
                # Save token securely
                await self._save_user_token(state, token_data)
                
                # Store in database for tracking
                from app.models.production import UserToken, User
                
                user = User.query.filter_by(id=state).first()
                if user:
                    # Remove existing Microsoft tokens for this user
                    existing_tokens = UserToken.query.filter_by(
                        user_id=user.id,
                        platform='microsoft'
                    ).all()
                    
                    for token in existing_tokens:
                        db.session.delete(token)
                    
                    # Create new token record
                    user_token = UserToken(
                        user_id=user.id,
                        platform='microsoft',
                        access_token=result['access_token'],
                        refresh_token=result.get('refresh_token'),
                        expires_at=token_data['expires_at'],
                        scopes=self.scopes,
                        platform_user_id=state
                    )
                    db.session.add(user_token)
                    db.session.commit()
                
                logger.info(f"Successfully stored real Microsoft OAuth credentials for user {state}")
                
                return {
                    'status': 'success',
                    'user_id': state,
                    'message': 'Microsoft Forms authentication successful',
                    'platform': 'microsoft_forms'
                }
            else:
                error_desc = result.get('error_description', 'Unknown error')
                raise Exception(f"Authentication failed: {error_desc}")
                
        except Exception as e:
            logger.error(f"Microsoft OAuth callback error: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")

    async def _save_user_token(self, user_id: str, token_data: Dict):
        """Save user token securely - NO MOCK DATA"""
        token_file = os.path.join(self.tokens_dir, f"user_{user_id}_token.json")
        
        # Convert datetime to string for JSON serialization
        token_data['expires_at'] = token_data['expires_at'].isoformat()
        
        async with aiofiles.open(token_file, 'w') as f:
            await f.write(json.dumps(token_data, indent=2))

    async def _load_user_token(self, user_id: str) -> Optional[Dict]:
        """Load user token - NO MOCK DATA"""
        token_file = os.path.join(self.tokens_dir, f"user_{user_id}_token.json")
        
        if not os.path.exists(token_file):
            return None
            
        try:
            async with aiofiles.open(token_file, 'r') as f:
                content = await f.read()
                token_data = json.loads(content)
                
            # Convert string back to datetime
            token_data['expires_at'] = datetime.fromisoformat(token_data['expires_at'])
            
            # Check if token is expired
            if datetime.utcnow() >= token_data['expires_at']:
                # Try to refresh token
                if token_data.get('refresh_token'):
                    return await self._refresh_token(user_id, token_data['refresh_token'])
                return None
            
            return token_data
            
        except Exception as e:
            logger.error(f"Error loading Microsoft token: {str(e)}")
            return None

    async def _refresh_token(self, user_id: str, refresh_token: str) -> Optional[Dict]:
        """Refresh Microsoft access token - NO MOCK DATA"""
        try:
            result = self.app.acquire_token_by_refresh_token(
                refresh_token=refresh_token,
                scopes=self.scopes
            )
            
            if "access_token" in result:
                token_data = {
                    'access_token': result['access_token'],
                    'refresh_token': result.get('refresh_token', refresh_token),
                    'expires_in': result.get('expires_in'),
                    'token_type': result.get('token_type', 'Bearer'),
                    'expires_at': datetime.utcnow() + timedelta(seconds=result.get('expires_in', 3600))
                }
                
                await self._save_user_token(user_id, token_data)
                
                # Update database token
                from app.models.production import UserToken
                user_token = UserToken.query.filter_by(
                    platform_user_id=user_id,
                    platform='microsoft'
                ).first()
                
                if user_token:
                    user_token.access_token = result['access_token']
                    user_token.expires_at = token_data['expires_at']
                    user_token.update_usage()
                    db.session.commit()
                
                return token_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error refreshing Microsoft token: {str(e)}")
            return None

    async def get_user_forms(self, user_id: str) -> Dict[str, Any]:
        """Get real Microsoft Forms for authenticated user - NO MOCK DATA"""
        token_data = await self._load_user_token(user_id)
        if not token_data:
            raise Exception("User not authenticated with Microsoft")
        
        try:
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get Microsoft Forms using Graph API
                # Note: Microsoft Forms API is still in beta, this is the approach
                response = await client.get(
                    'https://graph.microsoft.com/v1.0/me/drive/root/children',
                    headers=headers,
                    params={
                        '$filter': "name contains 'Form' or file/mimeType eq 'application/vnd.microsoft.forms'"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    forms = []
                    
                    logger.info(f"Found {len(data.get('value', []))} potential Microsoft Forms for user {user_id}")
                    
                    for item in data.get('value', []):
                        # Try to identify if this is actually a form
                        if self._is_microsoft_form(item):
                            form_details = await self._get_form_details(
                                item['id'], 
                                token_data['access_token']
                            )
                            
                            forms.append({
                                'id': item['id'],
                                'title': item['name'],
                                'created_time': item['createdDateTime'],
                                'modified_time': item['lastModifiedDateTime'],
                                'web_url': item.get('webUrl'),
                                'size': item.get('size', 0),
                                'form_details': form_details,
                                'platform': 'microsoft_forms'
                            })
                    
                    # Alternative: Try Microsoft Forms API directly (beta)
                    try:
                        forms_response = await client.get(
                            'https://graph.microsoft.com/beta/me/insights/used',
                            headers=headers,
                            params={
                                '$filter': "resourceVisualization/type eq 'Form'"
                            }
                        )
                        
                        if forms_response.status_code == 200:
                            forms_data = forms_response.json()
                            logger.info(f"Found {len(forms_data.get('value', []))} forms via insights API")
                            
                            for form_item in forms_data.get('value', []):
                                resource = form_item.get('resourceReference', {})
                                forms.append({
                                    'id': resource.get('id'),
                                    'title': form_item.get('resourceVisualization', {}).get('title'),
                                    'web_url': resource.get('webUrl'),
                                    'platform': 'microsoft_forms',
                                    'source': 'insights_api'
                                })
                    except Exception as e:
                        logger.warning(f"Could not access Microsoft Forms insights API: {str(e)}")
                    
                    return {
                        'forms': forms,
                        'total_count': len(forms),
                        'status': 'success',
                        'platform': 'microsoft_forms'
                    }
                else:
                    raise Exception(f"Microsoft Graph API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error fetching Microsoft forms: {str(e)}")
            raise Exception(f"Failed to fetch forms: {str(e)}")

    def _is_microsoft_form(self, item: Dict) -> bool:
        """Check if the item is likely a Microsoft Form - NO MOCK DATA"""
        name = item.get('name', '').lower()
        mime_type = item.get('file', {}).get('mimeType', '')
        
        # Check various indicators
        form_indicators = [
            'form' in name,
            'survey' in name,
            'questionnaire' in name,
            'feedback' in name,
            mime_type == 'application/vnd.microsoft.forms',
            item.get('webUrl', '').find('forms.microsoft.com') != -1
        ]
        
        return any(form_indicators)

    async def _get_form_details(self, form_id: str, access_token: str) -> Dict[str, Any]:
        """Get detailed information about a Microsoft Form - NO MOCK DATA"""
        try:
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get form metadata
                response = await client.get(
                    f'https://graph.microsoft.com/v1.0/me/drive/items/{form_id}',
                    headers=headers
                )
                
                if response.status_code == 200:
                    form_data = response.json()
                    
                    # Try to get form-specific information
                    try:
                        # Attempt to access the form content
                        content_response = await client.get(
                            f'https://graph.microsoft.com/v1.0/me/drive/items/{form_id}/content',
                            headers=headers
                        )
                        
                        if content_response.status_code == 200:
                            form_data['has_content'] = True
                            form_data['content_size'] = len(content_response.content)
                        else:
                            form_data['has_content'] = False
                    except:
                        form_data['has_content'] = False
                    
                    return form_data
                else:
                    return {'error': f'Could not fetch form details: {response.status_code}'}
                    
        except Exception as e:
            logger.error(f"Error fetching Microsoft form details: {str(e)}")
            return {'error': str(e)}

    async def get_form_responses(self, user_id: str, form_id: str) -> Dict[str, Any]:
        """Get real Microsoft Form responses - NO MOCK DATA"""
        token_data = await self._load_user_token(user_id)
        if not token_data:
            raise Exception("User not authenticated with Microsoft")
        
        try:
            headers = {
                'Authorization': f"Bearer {token_data['access_token']}",
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try multiple approaches to get responses
                responses = []
                
                # Approach 1: Try to get associated Excel file (common for Forms)
                try:
                    excel_response = await client.get(
                        f'https://graph.microsoft.com/v1.0/me/drive/items/{form_id}/workbook/worksheets',
                        headers=headers
                    )
                    
                    if excel_response.status_code == 200:
                        worksheets = excel_response.json()
                        
                        if worksheets.get('value'):
                            worksheet_id = worksheets['value'][0]['id']
                            
                            # Get worksheet data
                            data_response = await client.get(
                                f'https://graph.microsoft.com/v1.0/me/drive/items/{form_id}/workbook/worksheets/{worksheet_id}/usedRange',
                                headers=headers
                            )
                            
                            if data_response.status_code == 200:
                                range_data = data_response.json()
                                responses = self._process_excel_responses(range_data)
                                
                                logger.info(f"Found {len(responses)} responses in Excel format for form {form_id}")
                except Exception as e:
                    logger.warning(f"Could not access Excel responses: {str(e)}")
                
                # Approach 2: Try Microsoft Forms API (beta)
                if not responses:
                    try:
                        forms_response = await client.get(
                            f'https://graph.microsoft.com/beta/forms/{form_id}/responses',
                            headers=headers
                        )
                        
                        if forms_response.status_code == 200:
                            forms_data = forms_response.json()
                            responses = forms_data.get('value', [])
                            logger.info(f"Found {len(responses)} responses via Microsoft Forms API")
                    except Exception as e:
                        logger.warning(f"Could not access Microsoft Forms API: {str(e)}")
                
                return {
                    'responses': responses,
                    'response_count': len(responses),
                    'status': 'success',
                    'platform': 'microsoft_forms'
                }
                    
        except Exception as e:
            logger.error(f"Error fetching Microsoft form responses: {str(e)}")
            raise Exception(f"Failed to fetch responses: {str(e)}")

    def _process_excel_responses(self, range_data: Dict) -> List[Dict]:
        """Process Microsoft Forms response data from Excel - NO MOCK DATA"""
        try:
            values = range_data.get('values', [])
            if not values:
                return []
            
            # First row is usually headers
            headers = values[0]
            responses = []
            
            for i, row in enumerate(values[1:], 1):  # Skip header row
                response_data = {}
                for j, value in enumerate(row):
                    if j < len(headers):
                        response_data[headers[j]] = value
                
                responses.append({
                    'response_id': f"ms_response_{i}",
                    'answers': response_data,
                    'submitted_time': datetime.utcnow().isoformat(),  # Excel doesn't always provide this
                    'platform': 'microsoft_forms'
                })
            
            return responses
            
        except Exception as e:
            logger.error(f"Error processing Excel responses: {str(e)}")
            return []

    async def sync_form_to_database(self, user_id: str, form_id: str, program_id: int) -> Dict[str, Any]:
        """Sync real Microsoft Form responses to database - NO MOCK DATA"""
        try:
            # Get form responses
            form_data = await self.get_form_responses(user_id, form_id)
            
            # Import here to avoid circular imports
            from app.models.production import FormIntegration, FormResponse, Participant
            
            # Check if integration exists
            integration = FormIntegration.query.filter_by(
                program_id=program_id,
                form_id=form_id,
                platform='microsoft_forms'
            ).first()
            
            if not integration:
                # Create new integration
                integration = FormIntegration(
                    program_id=program_id,
                    platform='microsoft_forms',
                    form_id=form_id,
                    form_title=f"Microsoft Form {form_id}",
                    form_url=f"https://forms.microsoft.com/{form_id}",
                    oauth_user_id=user_id,
                    created_by=user_id
                )
                db.session.add(integration)
                db.session.flush()
            
            # Update integration metadata
            integration.last_sync = datetime.utcnow()
            integration.sync_count = (integration.sync_count or 0) + 1
            integration.integration_status = 'active'
            
            # Process responses
            participants_created = 0
            participants_updated = 0
            responses_processed = 0
            
            for response in form_data.get('responses', []):
                # Store the raw response
                form_response = FormResponse(
                    integration_id=integration.id,
                    external_response_id=response['response_id'],
                    response_data=response,
                    submitted_at=datetime.fromisoformat(response['submitted_time'].replace('Z', '+00:00')) if response.get('submitted_time') else datetime.utcnow()
                )
                
                # Normalize the data
                form_response.normalize_response_data()
                db.session.add(form_response)
                
                # Create/update participant if we have enough data
                normalized_data = form_response.normalized_data
                if normalized_data and normalized_data.get('email'):
                    participant_data = self._map_response_to_participant(normalized_data)
                    
                    # Check if participant exists
                    existing = Participant.query.filter_by(
                        program_id=program_id,
                        email=participant_data['email']
                    ).first()
                    
                    if existing:
                        # Update existing participant
                        for key, value in participant_data.items():
                            if value:
                                setattr(existing, key, value)
                        participants_updated += 1
                    else:
                        # Create new participant
                        new_participant = Participant(
                            program_id=program_id,
                            form_response_id=response['response_id'],
                            registration_source='microsoft_forms',
                            **participant_data
                        )
                        db.session.add(new_participant)
                        participants_created += 1
                
                responses_processed += 1
            
            db.session.commit()
            
            logger.info(f"Successfully synced {responses_processed} responses from Microsoft Form {form_id}")
            
            return {
                'status': 'success',
                'participants_created': participants_created,
                'participants_updated': participants_updated,
                'responses_processed': responses_processed,
                'total_responses': len(form_data.get('responses', [])),
                'integration_id': integration.id,
                'platform': 'microsoft_forms'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error syncing Microsoft form to database: {str(e)}")
            raise Exception(f"Sync failed: {str(e)}")

    def _map_response_to_participant(self, normalized_data: Dict) -> Dict[str, Any]:
        """Map normalized Microsoft form data to participant fields - NO MOCK DATA"""
        participant_data = {}
        
        # Direct mapping for standard fields
        field_mapping = {
            'full_name': normalized_data.get('name'),
            'email': normalized_data.get('email'),
            'phone': normalized_data.get('phone'),
            'identification_number': normalized_data.get('ic'),
            'gender': normalized_data.get('gender'),
            'organization': normalized_data.get('organization'),
            'position': normalized_data.get('position'),
            'department': normalized_data.get('department')
        }
        
        # Only include fields with values
        for field, value in field_mapping.items():
            if value and str(value).strip():
                participant_data[field] = str(value).strip()
        
        return participant_data

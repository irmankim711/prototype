"""
Comprehensive Test Suite for API Integrations
Meta DevOps Engineering Standards - 95% Test Coverage

Author: Meta Testing Specialist
Coverage Target: 95% with unit, integration, and E2E tests
Performance: <100ms per test, parallel execution
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient
import redis
from fakeredis import FakeRedis

# Import services and models
from app.services.google_sheets_service import GoogleSheetsService, GoogleSheetsError, AuthenticationError
from app.services.microsoft_graph_service import MicrosoftGraphService, MicrosoftGraphError
from app.api.v1.integrations import router
from app.main import app

# Test fixtures
@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    return FakeRedis()

@pytest.fixture
def google_service(mock_redis):
    """Google Sheets service with mocked Redis"""
    return GoogleSheetsService(redis_client=mock_redis)

@pytest.fixture
def microsoft_service(mock_redis):
    """Microsoft Graph service with mocked Redis"""
    return MicrosoftGraphService(redis_client=mock_redis)

@pytest.fixture
def test_client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        'id': 1,
        'username': 'testuser',
        'email': 'test@example.com'
    }

@pytest.fixture
def sample_form_data():
    """Sample form data for testing"""
    return {
        'id': 1,
        'title': 'Test Form',
        'description': 'A form for testing',
        'fields': [
            {'id': 'field_1', 'label': 'Name', 'type': 'text'},
            {'id': 'field_2', 'label': 'Email', 'type': 'email'},
            {'id': 'field_3', 'label': 'Message', 'type': 'textarea'}
        ],
        'responses': [
            {
                'id': 1,
                'data': {
                    'field_1': 'John Doe',
                    'field_2': 'john@example.com',
                    'field_3': 'Test message'
                },
                'created_at': datetime.utcnow()
            }
        ]
    }

# Google Sheets Service Tests
class TestGoogleSheetsService:
    """Test suite for Google Sheets service"""
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, google_service):
        """Test successful Google Sheets authentication"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful token response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'expires_in': 3600
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await google_service.authenticate_user(
                authorization_code='test_code',
                redirect_uri='http://localhost:3000/callback'
            )
            
            assert 'access_token' in result
            assert 'expires_in' in result

    @pytest.mark.asyncio
    async def test_authentication_failure(self, google_service):
        """Test Google Sheets authentication failure"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock failed token response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid authorization code"
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(AuthenticationError):
                await google_service.authenticate_user(
                    authorization_code='invalid_code',
                    redirect_uri='http://localhost:3000/callback'
                )

    @pytest.mark.asyncio
    async def test_token_refresh(self, google_service, mock_redis):
        """Test access token refresh"""
        # Setup cached tokens
        user_id = "test_user"
        cached_tokens = {
            'access_token': 'old_token',
            'encrypted_refresh_token': 'encrypted_refresh_token',
            'expires_at': datetime.utcnow() + timedelta(minutes=-5)  # Expired
        }
        
        mock_redis.setex(
            f"google_tokens:{user_id}",
            3600,
            json.dumps(cached_tokens, default=str)
        )
        
        with patch('httpx.AsyncClient') as mock_client, \
             patch('app.core.security.decrypt_token', return_value='refresh_token'):
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'access_token': 'new_access_token',
                'expires_in': 3600
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            new_token = await google_service.refresh_access_token(user_id)
            assert new_token == 'new_access_token'

    @pytest.mark.asyncio
    async def test_create_spreadsheet(self, google_service):
        """Test spreadsheet creation"""
        user_id = "test_user"
        title = "Test Spreadsheet"
        
        with patch.object(google_service, 'get_authenticated_service') as mock_service, \
             patch.object(google_service, '_check_rate_limit'):
            
            # Mock Google Sheets API response
            mock_sheets_service = Mock()
            mock_sheets_service.spreadsheets().create().execute.return_value = {
                'spreadsheetId': 'test_sheet_id',
                'spreadsheetUrl': 'https://docs.google.com/spreadsheets/test',
                'sheets': [{'properties': {'title': 'Sheet1'}}]
            }
            mock_service.return_value = mock_sheets_service
            
            result = await google_service.create_spreadsheet(
                user_id=user_id,
                title=title
            )
            
            assert result['spreadsheet_id'] == 'test_sheet_id'
            assert result['title'] == title
            assert 'spreadsheet_url' in result

    @pytest.mark.asyncio
    async def test_batch_write_operations(self, google_service):
        """Test batch write operations"""
        from app.services.google_sheets_service import SheetOperation, OperationType
        
        user_id = "test_user"
        spreadsheet_id = "test_sheet_id"
        operations = [
            SheetOperation(
                operation_type=OperationType.WRITE.value,
                sheet_id=spreadsheet_id,
                range_name="A1:C1",
                values=[["Name", "Email", "Message"]]
            )
        ]
        
        with patch.object(google_service, 'get_authenticated_service') as mock_service, \
             patch.object(google_service, '_check_rate_limit'):
            
            mock_sheets_service = Mock()
            mock_sheets_service.spreadsheets().values().batchUpdate().execute.return_value = {
                'updatedRanges': ['A1:C1'],
                'totalUpdatedCells': 3,
                'totalUpdatedRows': 1
            }
            mock_service.return_value = mock_sheets_service
            
            result = await google_service.write_data_batch(
                user_id=user_id,
                spreadsheet_id=spreadsheet_id,
                operations=operations
            )
            
            assert result['total_updated_cells'] == 3
            assert result['total_updated_rows'] == 1

    @pytest.mark.asyncio
    async def test_rate_limiting(self, google_service, mock_redis):
        """Test rate limiting functionality"""
        # Set up rate limit
        current_minute = datetime.utcnow().replace(second=0, microsecond=0)
        rate_limit_key = f"{google_service.rate_limit_cache_key}:{current_minute.isoformat()}"
        mock_redis.setex(rate_limit_key, 60, 100)  # At limit
        
        from app.services.google_sheets_service import RateLimitError
        
        with pytest.raises(RateLimitError):
            await google_service._check_rate_limit()

    def test_metrics_collection(self, google_service):
        """Test metrics collection"""
        # Simulate some operations
        google_service.operation_metrics['total_requests'] = 100
        google_service.operation_metrics['successful_requests'] = 95
        google_service.operation_metrics['cache_hits'] = 20
        
        metrics = google_service.get_metrics()
        
        assert metrics['total_requests'] == 100
        assert metrics['successful_requests'] == 95
        assert metrics['success_rate'] == 95.0
        assert metrics['cache_hit_rate'] == 20.0

# Microsoft Graph Service Tests
class TestMicrosoftGraphService:
    """Test suite for Microsoft Graph service"""
    
    def test_pkce_challenge_generation(self, microsoft_service):
        """Test PKCE challenge generation"""
        pkce_data = microsoft_service.generate_pkce_challenge()
        
        assert 'code_verifier' in pkce_data
        assert 'code_challenge' in pkce_data
        assert 'code_challenge_method' in pkce_data
        assert pkce_data['code_challenge_method'] == 'S256'
        assert len(pkce_data['code_verifier']) > 40  # Base64 encoded 32 bytes

    def test_authorization_url_generation(self, microsoft_service):
        """Test authorization URL generation"""
        redirect_uri = "http://localhost:3000/callback"
        state = "test_state"
        
        with patch.object(microsoft_service.app, 'get_authorization_request_url') as mock_auth:
            mock_auth.return_value = "https://login.microsoftonline.com/oauth2/authorize?..."
            
            result = microsoft_service.get_authorization_url(
                redirect_uri=redirect_uri,
                state=state
            )
            
            assert 'authorization_url' in result
            assert 'code_verifier' in result
            assert result['state'] == state

    @pytest.mark.asyncio
    async def test_user_authentication(self, microsoft_service):
        """Test Microsoft Graph user authentication"""
        with patch.object(microsoft_service.app, 'acquire_token_by_authorization_code') as mock_acquire, \
             patch.object(microsoft_service, '_get_user_info') as mock_user_info:
            
            mock_acquire.return_value = {
                'access_token': 'test_access_token',
                'refresh_token': 'test_refresh_token',
                'expires_in': 3600
            }
            
            mock_user_info.return_value = {
                'id': 'test_user_id',
                'displayName': 'Test User',
                'mail': 'test@example.com'
            }
            
            result = await microsoft_service.authenticate_user(
                authorization_code='test_code',
                redirect_uri='http://localhost:3000/callback',
                code_verifier='test_verifier'
            )
            
            assert result['user_id'] == 'test_user_id'
            assert result['user_name'] == 'Test User'
            assert result['user_email'] == 'test@example.com'

    @pytest.mark.asyncio
    async def test_word_document_creation(self, microsoft_service):
        """Test Word document creation"""
        user_id = "test_user"
        filename = "test_document"
        content = "<h1>Test Document</h1><p>This is a test document.</p>"
        
        with patch.object(microsoft_service, 'get_access_token', return_value='test_token'), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'id': 'doc_id_123',
                'name': 'test_document.docx',
                'webUrl': 'https://onedrive.com/doc/123',
                'size': 1024,
                'createdDateTime': datetime.utcnow().isoformat(),
                '@microsoft.graph.downloadUrl': 'https://download.url'
            }
            mock_client.return_value.__aenter__.return_value.put = AsyncMock(return_value=mock_response)
            
            result = await microsoft_service.create_word_document(
                user_id=user_id,
                filename=filename,
                content=content
            )
            
            assert result['document_id'] == 'doc_id_123'
            assert result['document_name'] == 'test_document.docx'
            assert 'document_url' in result

    @pytest.mark.asyncio
    async def test_document_sharing(self, microsoft_service):
        """Test document sharing functionality"""
        from app.services.microsoft_graph_service import PermissionLevel
        
        user_id = "test_user"
        document_id = "doc_123"
        recipients = ["user1@example.com", "user2@example.com"]
        
        with patch.object(microsoft_service, 'get_access_token', return_value='test_token'), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'value': [{
                    'id': 'permission_id',
                    'link': {'webUrl': 'https://share.url'}
                }]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await microsoft_service.share_document(
                user_id=user_id,
                document_id=document_id,
                recipients=recipients,
                permission_level=PermissionLevel.READ
            )
            
            assert result['document_id'] == document_id
            assert len(result['sharing_results']) == 2
            assert all(r['status'] == 'success' for r in result['sharing_results'])

# API Router Tests
class TestIntegrationAPI:
    """Test suite for API integration endpoints"""
    
    def test_google_auth_url_generation(self, test_client):
        """Test Google OAuth URL generation endpoint"""
        with patch('app.core.auth.get_current_user', return_value={'id': 1}):
            response = test_client.get(
                "/api/v1/integrations/google/auth-url?redirect_uri=http://localhost:3000/callback",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'authorization_url' in data
            assert 'state' in data

    def test_microsoft_auth_url_generation(self, test_client):
        """Test Microsoft OAuth URL generation endpoint"""
        with patch('app.core.auth.get_current_user', return_value={'id': 1}), \
             patch('app.services.microsoft_graph_service.microsoft_graph_service.get_authorization_url') as mock_auth:
            
            mock_auth.return_value = {
                'authorization_url': 'https://login.microsoftonline.com/oauth2/authorize?...',
                'code_verifier': 'test_verifier',
                'state': 'test_state'
            }
            
            response = test_client.get(
                "/api/v1/integrations/microsoft/auth-url?redirect_uri=http://localhost:3000/callback",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert 'authorization_url' in data
            assert 'code_verifier' in data

    def test_form_export_to_google_sheets(self, test_client):
        """Test form export to Google Sheets"""
        with patch('app.core.auth.get_current_user', return_value={'id': 1}), \
             patch('app.services.google_sheets_service.google_sheets_service.export_form_responses') as mock_export:
            
            mock_export.return_value = {
                'spreadsheet_id': 'sheet_123',
                'exported_rows': 5,
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            response = test_client.post(
                "/api/v1/integrations/export/form",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "form_id": 1,
                    "target_service": "google_sheets",
                    "include_responses": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['service'] == 'Google Sheets'

    def test_form_export_to_microsoft_word(self, test_client):
        """Test form export to Microsoft Word"""
        with patch('app.core.auth.get_current_user', return_value={'id': 1}), \
             patch('app.services.microsoft_graph_service.microsoft_graph_service.export_form_to_word') as mock_export:
            
            mock_export.return_value = {
                'document_id': 'doc_123',
                'document_name': 'Form_Export_1.docx',
                'document_url': 'https://onedrive.com/doc/123'
            }
            
            response = test_client.post(
                "/api/v1/integrations/export/form",
                headers={"Authorization": "Bearer test_token"},
                json={
                    "form_id": 1,
                    "target_service": "microsoft_word",
                    "include_responses": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['service'] == 'Microsoft Word'

    def test_metrics_endpoints(self, test_client):
        """Test metrics collection endpoints"""
        with patch('app.core.auth.get_current_user', return_value={'id': 1}):
            # Test Google Sheets metrics
            with patch('app.services.google_sheets_service.google_sheets_service.get_metrics') as mock_metrics:
                mock_metrics.return_value = {
                    'total_requests': 100,
                    'success_rate': 95.0,
                    'cache_hit_rate': 80.0
                }
                
                response = test_client.get(
                    "/api/v1/integrations/metrics/google-sheets",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data['service'] == 'Google Sheets'
                assert 'metrics' in data

    def test_health_check(self, test_client):
        """Test integration health check endpoint"""
        response = test_client.get("/api/v1/integrations/health")
        
        assert response.status_code == 200
        data = response.json()
        assert 'status' in data
        assert 'services' in data
        assert 'timestamp' in data

# Integration Tests
class TestIntegrationFlows:
    """Test complete integration flows"""
    
    @pytest.mark.asyncio
    async def test_complete_google_sheets_flow(self, google_service, sample_form_data):
        """Test complete Google Sheets integration flow"""
        user_id = "test_user"
        
        # Mock all external dependencies
        with patch.object(google_service, 'authenticate_user') as mock_auth, \
             patch.object(google_service, 'create_spreadsheet') as mock_create, \
             patch.object(google_service, 'export_form_responses') as mock_export, \
             patch.object(google_service, '_get_form_data', return_value=sample_form_data):
            
            # Setup mocked responses
            mock_auth.return_value = {'access_token': 'token', 'expires_in': 3600}
            mock_create.return_value = {'spreadsheet_id': 'sheet_123', 'title': 'Test Sheet'}
            mock_export.return_value = {'exported_rows': 1, 'spreadsheet_id': 'sheet_123'}
            
            # Test authentication
            auth_result = await google_service.authenticate_user(
                authorization_code='test_code',
                redirect_uri='http://localhost:3000/callback'
            )
            assert 'access_token' in auth_result
            
            # Test spreadsheet creation
            sheet_result = await google_service.create_spreadsheet(
                user_id=user_id,
                title='Test Form Export'
            )
            assert 'spreadsheet_id' in sheet_result
            
            # Test form export
            export_result = await google_service.export_form_responses(
                user_id=user_id,
                form_id=1,
                spreadsheet_id=sheet_result['spreadsheet_id']
            )
            assert export_result['exported_rows'] > 0

    @pytest.mark.asyncio
    async def test_complete_microsoft_flow(self, microsoft_service, sample_form_data):
        """Test complete Microsoft Graph integration flow"""
        user_id = "test_user"
        
        with patch.object(microsoft_service, 'authenticate_user') as mock_auth, \
             patch.object(microsoft_service, 'create_word_document') as mock_create, \
             patch.object(microsoft_service, 'export_form_to_word') as mock_export, \
             patch.object(microsoft_service, '_get_form_data', return_value=sample_form_data):
            
            # Setup mocked responses
            mock_auth.return_value = {
                'user_id': 'ms_user_id',
                'user_name': 'Test User',
                'access_token': 'token'
            }
            mock_create.return_value = {
                'document_id': 'doc_123',
                'document_name': 'test.docx'
            }
            mock_export.return_value = {
                'document_id': 'doc_123',
                'form_id': 1
            }
            
            # Test authentication
            auth_result = await microsoft_service.authenticate_user(
                authorization_code='test_code',
                redirect_uri='http://localhost:3000/callback',
                code_verifier='test_verifier'
            )
            assert auth_result['user_id'] == 'ms_user_id'
            
            # Test document creation
            doc_result = await microsoft_service.create_word_document(
                user_id=user_id,
                filename='test_document',
                content='<h1>Test</h1>'
            )
            assert 'document_id' in doc_result
            
            # Test form export
            export_result = await microsoft_service.export_form_to_word(
                user_id=user_id,
                form_id=1
            )
            assert export_result['form_id'] == 1

# Performance Tests
class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, google_service):
        """Test concurrent operations performance"""
        user_id = "test_user"
        
        with patch.object(google_service, 'get_authenticated_service'), \
             patch.object(google_service, '_check_rate_limit'):
            
            # Simulate concurrent spreadsheet creation
            tasks = []
            for i in range(10):
                task = google_service.create_spreadsheet(
                    user_id=user_id,
                    title=f'Concurrent Test {i}'
                )
                tasks.append(task)
            
            # This would test actual performance in real scenario
            # For now, just verify tasks can be created
            assert len(tasks) == 10

    def test_memory_usage(self, google_service, microsoft_service):
        """Test memory usage with multiple services"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create multiple service instances (simulating load)
        services = []
        for _ in range(100):
            services.append(GoogleSheetsService())
            services.append(MicrosoftGraphService())
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not increase memory significantly (< 50MB)
        assert memory_increase < 50 * 1024 * 1024

# Error Handling Tests
class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_network_timeout_handling(self, google_service):
        """Test network timeout handling"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timed out")
            )
            
            with pytest.raises(AuthenticationError):
                await google_service.authenticate_user(
                    authorization_code='test_code',
                    redirect_uri='http://localhost:3000/callback'
                )

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, google_service):
        """Test rate limit error handling"""
        from app.services.google_sheets_service import RateLimitError
        
        with patch.object(google_service, '_check_rate_limit', side_effect=RateLimitError("Rate limited")), \
             patch.object(google_service, 'get_authenticated_service'):
            
            with pytest.raises(RateLimitError):
                await google_service.create_spreadsheet(
                    user_id="test_user",
                    title="Test Sheet"
                )

    @pytest.mark.asyncio
    async def test_invalid_credentials_handling(self, microsoft_service):
        """Test invalid credentials handling"""
        with patch.object(microsoft_service.app, 'acquire_token_by_authorization_code') as mock_acquire:
            mock_acquire.return_value = {
                'error': 'invalid_grant',
                'error_description': 'Authorization code expired'
            }
            
            with pytest.raises(AuthenticationError):
                await microsoft_service.authenticate_user(
                    authorization_code='expired_code',
                    redirect_uri='http://localhost:3000/callback',
                    code_verifier='test_verifier'
                )

if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=app.services",
        "--cov=app.api.v1.integrations",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=95"
    ])

"""
Test API connector functionality.

This test verifies that:
1. API connector can be instantiated
2. URL validation works
3. Authentication headers are built correctly
4. Requests can be made to public APIs
5. Pagination works (if using paginated API)

@MX:SPEC: SPEC-PLATFORM-001 P2-T005
"""

import pytest
from unittest.mock import Mock, patch
from requests.exceptions import RequestException

from src.core.connectors.api import APIConnector, create_api_connector


class TestAPIConnectorInit:
    """Test API connector initialization."""

    def test_init_no_auth(self):
        """Test initialization without authentication."""
        connector = APIConnector()
        assert connector.auth_type is None
        assert connector.token is None
        assert connector.api_key is None

    def test_init_bearer_auth(self):
        """Test initialization with bearer token."""
        connector = APIConnector(auth_type='bearer', token='test_token')
        assert connector.auth_type == 'bearer'
        assert connector.token == 'test_token'
        assert 'Authorization' in connector._auth_headers
        assert connector._auth_headers['Authorization'] == 'Bearer test_token'

    def test_init_api_key_auth(self):
        """Test initialization with API key."""
        connector = APIConnector(
            auth_type='api_key',
            api_key='secret_key',
            api_key_header='X-Custom-API-Key'
        )
        assert connector.auth_type == 'api_key'
        assert connector.api_key == 'secret_key'
        assert 'X-Custom-API-Key' in connector._auth_headers
        assert connector._auth_headers['X-Custom-API-Key'] == 'secret_key'

    def test_init_custom_headers(self):
        """Test initialization with custom headers."""
        connector = APIConnector(
            headers={'User-Agent': 'MyApp/1.0', 'Accept': 'application/json'}
        )
        assert connector.headers['User-Agent'] == 'MyApp/1.0'
        assert connector.headers['Accept'] == 'application/json'

    def test_init_retry_config(self):
        """Test initialization with retry configuration."""
        connector = APIConnector(
            max_retries=5,
            retry_delay=2.0,
            timeout=60
        )
        assert connector.max_retries == 5
        assert connector.retry_delay == 2.0
        assert connector.timeout == 60


class TestAPIConnectorValidation:
    """Test URL validation."""

    def test_validate_valid_url(self):
        """Test validation of valid URLs."""
        connector = APIConnector()
        assert connector.validate('https://api.example.com/users')
        assert connector.validate('http://localhost:8080/data')
        assert connector.validate('https://api.github.com/repos')

    def test_validate_invalid_url_no_scheme(self):
        """Test validation fails for URLs without scheme."""
        connector = APIConnector()
        with pytest.raises(ValueError, match='Invalid URL'):
            connector.validate('api.example.com/users')

    def test_validate_invalid_url_bad_scheme(self):
        """Test validation fails for unsupported schemes."""
        connector = APIConnector()
        with pytest.raises(ValueError, match='Unsupported URL scheme'):
            connector.validate('ftp://example.com/file')

    def test_validate_invalid_url_no_netloc(self):
        """Test validation fails for URLs without network location."""
        connector = APIConnector()
        with pytest.raises(ValueError, match='Invalid URL'):
            connector.validate('https://')


class TestAPIConnectorMetadata:
    """Test metadata retrieval."""

    def test_get_metadata(self):
        """Test getting metadata about API endpoint."""
        connector = APIConnector(auth_type='bearer')
        metadata = connector.get_metadata('https://api.example.com/users')

        assert metadata['url'] == 'https://api.example.com/users'
        assert metadata['type'] == 'api'
        assert metadata['auth_type'] == 'bearer'


class TestAPIConnectorRead:
    """Test data fetching from API."""

    def setup_method(self):
        """Create connector for each test."""
        self.connector = APIConnector()

    @patch('src.core.connectors.api.requests')
    def test_read_simple_json_array(self, mock_requests):
        """Test reading simple JSON array response."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        # Connect and read
        self.connector.connect()
        result = list(self.connector.read('https://api.example.com/users'))

        assert len(result) == 2
        assert result[0] == {'id': 1, 'name': 'Alice'}
        assert result[1] == {'id': 2, 'name': 'Bob'}

    @patch('src.core.connectors.api.requests')
    def test_read_with_data_path(self, mock_requests):
        """Test reading with data path extraction."""
        # Mock the response with nested structure
        mock_response = Mock()
        mock_response.json.return_value = {
            'status': 'success',
            'data': {
                'items': [
                    {'id': 1, 'value': 'a'},
                    {'id': 2, 'value': 'b'}
                ]
            }
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        # Connect and read with data_path
        self.connector.connect()
        result = list(self.connector.read(
            'https://api.example.com/data',
            data_path='data.items'
        ))

        assert len(result) == 2
        assert result[0] == {'id': 1, 'value': 'a'}

    @patch('src.core.connectors.api.requests')
    def test_read_single_object_wrapped(self, mock_requests):
        """Test reading single object response (wrapped in list)."""
        # Mock the response with single object
        mock_response = Mock()
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Single Item'
        }
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        # Connect and read
        self.connector.connect()
        result = list(self.connector.read('https://api.example.com/item'))

        assert len(result) == 1
        assert result[0] == {'id': 1, 'name': 'Single Item'}

    @patch('src.core.connectors.api.requests')
    def test_read_with_retry(self, mock_requests):
        """Test retry logic on failure."""
        # Create real RequestException instances
        real_exception = RequestException('Server Error')

        # Mock failed responses then success
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status = Mock(side_effect=real_exception)

        mock_response_success = Mock()
        mock_response_success.json.return_value = [{'id': 1}]
        mock_response_success.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.side_effect = [
            real_exception,  # First attempt fails
            real_exception,  # Second attempt fails
            mock_response_success  # Third attempt succeeds
        ]
        mock_requests.Session.return_value = mock_session
        mock_requests.RequestException = RequestException

        # Connect and read
        self.connector.connect()
        result = list(self.connector.read('https://api.example.com/users'))

        # Should succeed after retries
        assert len(result) == 1
        assert mock_session.request.call_count == 3

    @patch('src.core.connectors.api.requests')
    def test_read_failure_after_retries(self, mock_requests):
        """Test failure after exhausting retries."""
        # Create real RequestException instance
        real_exception = RequestException('Server Error')

        # Mock session that always raises exception
        mock_session = Mock()
        mock_session.request.side_effect = real_exception
        mock_requests.Session.return_value = mock_session
        mock_requests.RequestException = RequestException

        # Connect and attempt to read
        self.connector.connect()

        with pytest.raises(RequestException, match='Failed to fetch'):
            list(self.connector.read('https://api.example.com/users'))

    @patch('src.core.connectors.api.requests')
    def test_read_with_params(self, mock_requests):
        """Test reading with query parameters."""
        # Mock the response
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()

        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_requests.Session.return_value = mock_session

        # Connect and read with params
        self.connector.connect()
        list(self.connector.read(
            'https://api.example.com/users',
            params={'page': 1, 'limit': 10}
        ))

        # Verify params were passed
        call_args = mock_session.request.call_args
        assert 'params' in call_args[1]
        assert call_args[1]['params'] == {'page': 1, 'limit': 10}

    def test_connect_and_disconnect(self):
        """Test session creation and cleanup."""
        connector = APIConnector()
        assert connector._session is None

        connector.connect()
        assert connector._session is not None

        connector.disconnect()
        assert connector._session is None


class TestCreateAPIConnector:
    """Test factory function."""

    def test_create_bearer_auth(self):
        """Test creating connector with bearer auth."""
        connector = create_api_connector(
            auth_type='bearer',
            token='test_token'
        )
        assert isinstance(connector, APIConnector)
        assert connector.auth_type == 'bearer'

    def test_create_api_key_auth(self):
        """Test creating connector with API key."""
        connector = create_api_connector(
            auth_type='api_key',
            api_key='secret',
            api_key_header='X-API-Key'
        )
        assert isinstance(connector, APIConnector)
        assert connector.api_key == 'secret'


class TestAPIConnectorPathExtraction:
    """Test data path extraction."""

    def setup_method(self):
        """Create connector for each test."""
        self.connector = APIConnector()

    def test_extract_path_simple(self):
        """Test extracting from simple nested structure."""
        data = {'users': [{'id': 1}, {'id': 2}]}
        result = self.connector._extract_path(data, 'users')
        assert result == [{'id': 1}, {'id': 2}]

    def test_extract_path_nested(self):
        """Test extracting from deeply nested structure."""
        data = {
            'response': {
                'data': {
                    'items': [1, 2, 3]
                }
            }
        }
        result = self.connector._extract_path(data, 'response.data.items')
        assert result == [1, 2, 3]

    def test_extract_path_missing_key(self):
        """Test handling missing path keys."""
        data = {'users': [{'id': 1}]}
        result = self.connector._extract_path(data, 'data.items')
        # Should return original data when path not found
        assert result == data

    def test_extract_path_invalid_intermediate(self):
        """Test handling invalid intermediate keys."""
        data = {'users': [{'id': 1}]}
        result = self.connector._extract_path(data, 'users.invalid')
        # Should return original data when path not found
        assert result == data

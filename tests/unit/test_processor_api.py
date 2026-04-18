"""
Test Processor.load_api() method.

This test verifies that:
1. API data can be loaded into Processor
2. The load_api method properly uses the APIConnector
3. Authentication parameters are passed through
4. Query parameters work
5. Data path extraction works

@MX:SPEC: SPEC-PLATFORM-001 P2-T005
"""

import pytest
from unittest.mock import Mock, patch

from src.core.processor import Processor


class TestProcessorLoadAPI:
    """Test Processor.load_api() method."""

    @pytest.fixture
    def processor(self):
        """Create a Processor instance for testing."""
        return Processor()

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_basic(self, mock_connector_class, processor):
        """Test basic API loading without authentication."""
        # Mock the connector
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ])
        mock_connector_class.return_value = mock_connector

        # Load API data
        result = processor.load_api('https://api.example.com/users')

        # Verify connector was created correctly
        mock_connector_class.assert_called_once()
        mock_connector.validate.assert_called_once_with('https://api.example.com/users')
        mock_connector.connect.assert_called_once()
        mock_connector.disconnect.assert_called_once()

        # Verify result
        assert not result.empty
        assert len(result) == 2

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_bearer_auth(self, mock_connector_class, processor):
        """Test API loading with bearer token authentication."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with bearer auth
        result = processor.load_api(
            'https://api.example.com/users',
            auth_type='bearer',
            token='secret_token'
        )

        # Verify connector was created with auth
        call_kwargs = mock_connector_class.call_args[1]
        assert call_kwargs['auth_type'] == 'bearer'
        assert call_kwargs['token'] == 'secret_token'
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_api_key(self, mock_connector_class, processor):
        """Test API loading with API key authentication."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with API key
        result = processor.load_api(
            'https://api.example.com/data',
            auth_type='api_key',
            api_key='secret_key',
            api_key_header='X-Custom-API-Key'
        )

        # Verify connector was created with API key
        mock_connector_class.assert_called_once()
        call_kwargs = mock_connector_class.call_args[1]
        assert call_kwargs['auth_type'] == 'api_key'
        assert call_kwargs['api_key'] == 'secret_key'
        assert call_kwargs['api_key_header'] == 'X-Custom-API-Key'
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_params(self, mock_connector_class, processor):
        """Test API loading with query parameters."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with params
        result = processor.load_api(
            'https://api.example.com/users',
            params={'page': 2, 'limit': 50}
        )

        # Verify read was called with params
        mock_connector.read.assert_called_once()
        call_kwargs = mock_connector.read.call_args[1]
        assert call_kwargs['params'] == {'page': 2, 'limit': 50}
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_data_path(self, mock_connector_class, processor):
        """Test API loading with data path extraction."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with data_path
        result = processor.load_api(
            'https://api.example.com/data',
            data_path='response.data.items'
        )

        # Verify read was called with data_path
        mock_connector.read.assert_called_once()
        call_kwargs = mock_connector.read.call_args[1]
        assert call_kwargs['data_path'] == 'response.data.items'
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_pagination(self, mock_connector_class, processor):
        """Test API loading with pagination."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        # Simulate paginated response
        mock_connector.read = Mock(return_value=[
            {'id': 1}, {'id': 2}, {'id': 3}, {'id': 4}, {'id': 5}
        ])
        mock_connector_class.return_value = mock_connector

        # Load API data with pagination
        result = processor.load_api(
            'https://api.example.com/users',
            pagination='offset',
            max_pages=3
        )

        # Verify read was called with pagination params
        mock_connector.read.assert_called_once()
        call_kwargs = mock_connector.read.call_args[1]
        assert call_kwargs['pagination'] == 'offset'
        assert call_kwargs['max_pages'] == 3
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_custom_table_name(self, mock_connector_class, processor):
        """Test API loading with custom table name."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with custom table name
        result = processor.load_api(
            'https://api.example.com/users',
            table_name='api_users'
        )

        # Verify table name was set
        assert processor.table_name == 'api_users'
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_empty_response(self, mock_connector_class, processor):
        """Test API loading when API returns no data."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[])  # Empty response
        mock_connector_class.return_value = mock_connector

        # Should raise ValueError for empty response
        with pytest.raises(ValueError, match='API returned no data'):
            processor.load_api('https://api.example.com/empty')

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_custom_headers(self, mock_connector_class, processor):
        """Test API loading with custom headers."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with custom headers
        result = processor.load_api(
            'https://api.example.com/users',
            headers={'User-Agent': 'MyApp/1.0', 'Accept': 'application/json'}
        )

        # Verify connector was created with headers
        call_kwargs = mock_connector_class.call_args[1]
        assert call_kwargs['headers']['User-Agent'] == 'MyApp/1.0'
        assert call_kwargs['headers']['Accept'] == 'application/json'
        assert not result.empty

    @patch('src.core.connectors.api.APIConnector')
    def test_load_api_with_post_method(self, mock_connector_class, processor):
        """Test API loading with POST method."""
        mock_connector = Mock()
        mock_connector.validate = Mock()
        mock_connector.connect = Mock()
        mock_connector.disconnect = Mock()
        mock_connector.read = Mock(return_value=[{'id': 1}])
        mock_connector_class.return_value = mock_connector

        # Load API data with POST method
        result = processor.load_api(
            'https://api.example.com/search',
            method='POST'
        )

        # Verify read was called with POST method
        call_kwargs = mock_connector.read.call_args[1]
        assert call_kwargs['method'] == 'POST'
        assert not result.empty

import pytest
import requests
import time
import json
from unittest.mock import patch, MagicMock

PRODUCER_URL = "http://localhost:5000"

class TestProducerAPI:
    
    def test_health_endpoint(self):
        response = requests.get(f"{PRODUCER_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
    
    def test_metrics_endpoint(self):
        response = requests.get(f"{PRODUCER_URL}/metrics")
        assert response.status_code == 200
        assert 'messages_produced_total' in response.text
    
    def test_produce_single_message(self):
        payload = {
            "id": "test_msg_1",
            "payload": "Test message content"
        }
        
        response = requests.post(f"{PRODUCER_URL}/produce", json=payload)
        assert response.status_code == 201
        
        data = response.json()
        assert data['status'] == 'success'
        assert data['message_id'] == 'test_msg_1'
        assert 'timestamp' in data
    
    def test_produce_message_without_data(self):
        response = requests.post(f"{PRODUCER_URL}/produce")
        assert response.status_code == 400
        
        data = response.json()
        assert 'error' in data
    
    def test_batch_produce(self):
        payload = {
            "messages": [
                {"id": "batch_1", "payload": "Message 1"},
                {"id": "batch_2", "payload": "Message 2"},
                {"id": "batch_3", "payload": "Message 3"}
            ]
        }
        
        response = requests.post(f"{PRODUCER_URL}/batch-produce", json=payload)
        assert response.status_code == 201
        
        data = response.json()
        assert data['status'] == 'success'
        assert data['messages_produced'] == 3
    
    def test_batch_produce_without_messages(self):
        payload = {"invalid": "data"}
        
        response = requests.post(f"{PRODUCER_URL}/batch-produce", json=payload)
        assert response.status_code == 400
        
        data = response.json()
        assert 'error' in data

class TestRabbitMQClient:
    
    @patch('shared.rabbitmq_client.pika.BlockingConnection')
    def test_rabbitmq_connection_success(self, mock_connection):
        from shared.rabbitmq_client import RabbitMQClient
        
        mock_conn = MagicMock()
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel
        mock_connection.return_value = mock_conn
        
        client = RabbitMQClient()
        result = client.connect()
        
        assert result is True
        assert client.connection == mock_conn
        assert client.channel == mock_channel
    
    @patch('shared.rabbitmq_client.pika.BlockingConnection')
    def test_rabbitmq_connection_failure(self, mock_connection):
        from shared.rabbitmq_client import RabbitMQClient
        
        mock_connection.side_effect = Exception("Connection failed")
        
        client = RabbitMQClient()
        result = client.connect()
        
        assert result is False
        assert client.connection is None
        assert client.channel is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
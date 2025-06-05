import pika
import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.host = os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = int(os.getenv('RABBITMQ_PORT', 5672))
        self.username = os.getenv('RABBITMQ_USER', 'admin')
        self.password = os.getenv('RABBITMQ_PASS', 'password')
        self.connection = None
        self.channel = None
        
    def connect(self) -> bool:
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            logger.info("Connected to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False
    
    def declare_queue(self, queue_name: str, durable: bool = True):
        if not self.channel:
            raise Exception("Not connected to RabbitMQ")
        self.channel.queue_declare(queue=queue_name, durable=durable)
    
    def publish_message(self, queue_name: str, message: dict):
        if not self.channel:
            raise Exception("Not connected to RabbitMQ")
        
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        logger.info(f"Published message to {queue_name}: {message}")
    
    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            logger.info("Closed RabbitMQ connection")
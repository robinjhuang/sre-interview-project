import os
import sys
import json
import time
import signal
import logging
from datetime import datetime
import pika
from prometheus_client import Counter, Histogram, start_http_server

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.rabbitmq_client import RabbitMQClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
messages_processed = Counter('messages_consumed_total', 'Total messages consumed')
processing_duration = Histogram('message_processing_duration_seconds', 'Message processing duration')
processing_errors = Counter('message_processing_errors_total', 'Total message processing errors')

class MessageConsumer:
    def __init__(self):
        self.rabbitmq_client = None
        self.running = True
        
    def connect_rabbitmq(self):
        self.rabbitmq_client = RabbitMQClient()
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            if self.rabbitmq_client.connect():
                self.rabbitmq_client.declare_queue('task_queue')
                logger.info("Consumer connected to RabbitMQ")
                return True
            else:
                logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
        
        logger.error("Failed to connect to RabbitMQ after maximum retries")
        return False
    
    @processing_duration.time()
    def process_message(self, ch, method, properties, body):
        try:
            message = json.loads(body.decode('utf-8'))
            logger.info(f"Processing message: {message.get('id', 'unknown')}")
            
            # Simulate processing work
            processing_time = message.get('processing_time', 1)
            time.sleep(min(processing_time, 5))  # Cap at 5 seconds
            
            # Simulate random failures (10% chance)
            import random
            if random.random() < 0.1:
                raise Exception("Simulated processing error")
            
            logger.info(f"Successfully processed message: {message.get('id', 'unknown')}")
            messages_processed.inc()
            
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            processing_errors.inc()
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            processing_errors.inc()
            # Requeue the message for retry
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        if not self.connect_rabbitmq():
            return False
        
        # Set up consumer
        self.rabbitmq_client.channel.basic_qos(prefetch_count=1)
        self.rabbitmq_client.channel.basic_consume(
            queue='task_queue',
            on_message_callback=self.process_message
        )
        
        logger.info("Consumer started. Waiting for messages...")
        
        try:
            while self.running:
                # Process messages with timeout
                self.rabbitmq_client.connection.process_data_events(time_limit=1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        self.running = False
        if self.rabbitmq_client:
            self.rabbitmq_client.close()
        logger.info("Consumer stopped")

def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}")
    consumer.stop()

if __name__ == '__main__':
    # Start Prometheus metrics server
    start_http_server(8000)
    logger.info("Prometheus metrics server started on port 8000")
    
    # Set up signal handlers
    consumer = MessageConsumer()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start consuming
    consumer.start_consuming()
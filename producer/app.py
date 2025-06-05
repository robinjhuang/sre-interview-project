import os
import sys
import json
import time
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.rabbitmq_client import RabbitMQClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Prometheus metrics
message_counter = Counter('messages_produced_total', 'Total messages produced')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Global RabbitMQ client
rabbitmq_client = None

def init_rabbitmq():
    global rabbitmq_client
    rabbitmq_client = RabbitMQClient()
    max_retries = 10
    retry_delay = 5
    
    for attempt in range(max_retries):
        if rabbitmq_client.connect():
            rabbitmq_client.declare_queue('task_queue')
            logger.info("RabbitMQ initialized successfully")
            return True
        else:
            logger.warning(f"RabbitMQ connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
    
    logger.error("Failed to connect to RabbitMQ after maximum retries")
    return False

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/produce', methods=['POST'])
@request_duration.time()
def produce_message():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        message = {
            'id': data.get('id', f"msg_{int(time.time())}"),
            'payload': data.get('payload', ''),
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'producer-api'
        }
        
        rabbitmq_client.publish_message('task_queue', message)
        message_counter.inc()
        
        return jsonify({
            'status': 'success',
            'message_id': message['id'],
            'timestamp': message['timestamp']
        }), 201
        
    except Exception as e:
        logger.error(f"Error producing message: {e}")
        return jsonify({'error': 'Failed to produce message'}), 500

@app.route('/batch-produce', methods=['POST'])
@request_duration.time()
def batch_produce():
    try:
        data = request.get_json()
        if not data or 'messages' not in data:
            return jsonify({'error': 'No messages array provided'}), 400
        
        messages = data['messages']
        produced_count = 0
        
        for msg_data in messages:
            message = {
                'id': msg_data.get('id', f"batch_msg_{int(time.time())}_{produced_count}"),
                'payload': msg_data.get('payload', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'producer-api-batch'
            }
            
            rabbitmq_client.publish_message('task_queue', message)
            message_counter.inc()
            produced_count += 1
        
        return jsonify({
            'status': 'success',
            'messages_produced': produced_count
        }), 201
        
    except Exception as e:
        logger.error(f"Error in batch produce: {e}")
        return jsonify({'error': 'Failed to produce batch messages'}), 500

if __name__ == '__main__':
    if not init_rabbitmq():
        sys.exit(1)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
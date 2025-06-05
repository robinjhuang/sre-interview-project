# SRE Interview Project: Message Queue System

## Overview

This project implements a microservices architecture with a message producer and consumer using RabbitMQ. It's designed as an interview project for Site Reliability Engineering (SRE) candidates.

## Architecture

```
┌─────────────┐    HTTP     ┌─────────────┐    AMQP     ┌─────────────┐
│   Client    │ ───────────▶│  Producer   │ ───────────▶│  RabbitMQ   │
└─────────────┘             │  (Flask)    │             │   Queue     │
                            └─────────────┘             └─────────────┘
                                                               │
                                                               │ AMQP
                                                               ▼
                                                        ┌─────────────┐
                                                        │  Consumer   │
                                                        │  (Python)   │
                                                        └─────────────┘
```

## Components

### Producer Service (port 5000)
- **Flask API** with endpoints for message production
- **Prometheus metrics** for monitoring
- **Health checks** for service monitoring
- **Batch processing** capabilities

### Consumer Service (port 8000)
- **Message processing** with configurable delays
- **Error handling** and retry logic  
- **Prometheus metrics** for monitoring
- **Graceful shutdown** handling

### RabbitMQ (ports 5672, 15672)
- **Message broker** with persistence
- **Management UI** for queue monitoring
- **Health checks** and retry logic

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Make (optional, for convenience commands)

### Start the System

```bash
# Start all services
docker-compose up -d

# Or using make
make up

# Check service status
docker-compose ps
```

### Test the System

```bash
# Run the test suite
python scripts/test_system.py

# Send a single message
curl -X POST http://localhost:5000/produce \\
  -H "Content-Type: application/json" \\
  -d '{"id": "test1", "payload": "Hello World"}'

# Send batch messages
curl -X POST http://localhost:5000/batch-produce \\
  -H "Content-Type: application/json" \\
  -d '{
    "messages": [
      {"id": "batch1", "payload": "Message 1"},
      {"id": "batch2", "payload": "Message 2"}
    ]
  }'
```

### Monitor the System

- **Producer Health**: http://localhost:5000/health
- **Producer Metrics**: http://localhost:5000/metrics  
- **RabbitMQ Management**: http://localhost:15672 (admin/password)
- **Consumer Metrics**: http://localhost:8000/metrics

## API Documentation

### Producer Endpoints

#### Health Check
```
GET /health
Response: {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}
```

#### Produce Single Message
```
POST /produce
Body: {"id": "msg1", "payload": "content", "processing_time": 1.5}
Response: {"status": "success", "message_id": "msg1", "timestamp": "..."}
```

#### Batch Produce
```
POST /batch-produce  
Body: {"messages": [{"id": "msg1", "payload": "content"}, ...]}
Response: {"status": "success", "messages_produced": 2}
```

#### Metrics
```
GET /metrics
Response: Prometheus format metrics
```

## Development

### Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start RabbitMQ only
docker-compose up -d rabbitmq

# Run producer locally
cd producer && python app.py

# Run consumer locally  
cd consumer && python app.py
```

### Running Tests

```bash
# Integration tests
python -m pytest tests/ -v

# System tests
python scripts/test_system.py

# Load testing
python scripts/test_system.py  # includes concurrent load tests
```

### Useful Commands

```bash
# View logs
make logs

# Scale consumers
make scale-consumer  # scales to 3 consumer instances

# Clean up
make clean

# Monitor services
make monitor
```

## Metrics Available

### Producer Metrics
- `messages_produced_total` - Total messages produced
- `http_request_duration_seconds` - HTTP request latency

### Consumer Metrics  
- `messages_consumed_total` - Total messages consumed
- `message_processing_duration_seconds` - Processing time per message
- `message_processing_errors_total` - Processing error count

### RabbitMQ Metrics
- Queue depth, message rates, connection counts (via management plugin)

## Configuration

Environment variables can be set in `.env` file (see `.env.example`):

```bash
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=admin
RABBITMQ_PASS=password
FLASK_ENV=production
LOG_LEVEL=INFO
```

## Troubleshooting

### Common Issues

1. **Services not starting**: Check if ports 5000, 5672, 15672 are available
2. **Connection refused**: Wait for RabbitMQ to fully start (health check)
3. **Messages not processing**: Check consumer logs and RabbitMQ queue status
4. **Permission errors**: Ensure Docker daemon is running and accessible

### Debug Commands

```bash
# Check service health
curl http://localhost:5000/health

# View RabbitMQ queues
curl -u admin:password http://localhost:15672/api/queues

# Check consumer metrics
curl http://localhost:8000/metrics

# View detailed logs
docker-compose logs -f consumer
```

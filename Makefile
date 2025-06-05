.PHONY: up down logs build clean test

# Start all services
up:
	docker-compose up -d

# Stop all services  
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Build services
build:
	docker-compose build

# Clean up everything
clean:
	docker-compose down -v
	docker system prune -f

# Run local tests
test:
	python -m pytest tests/ -v

# Scale consumer service
scale-consumer:
	docker-compose up -d --scale consumer=3

# Monitor services
monitor:
	watch 'docker-compose ps && echo "\n=== Producer Health ===" && curl -s http://localhost:5000/health | jq .'
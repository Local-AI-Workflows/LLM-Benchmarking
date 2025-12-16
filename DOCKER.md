# Docker Setup Guide

This guide explains how to use Docker Compose to run MongoDB and optionally the API server.

## Quick Start

```bash
# Start MongoDB
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f mongodb

# Stop MongoDB
docker-compose down
```

## MongoDB Service

The `docker-compose.yml` includes a MongoDB service with:

- **Image**: `mongo:7.0` (latest stable version)
- **Port**: `27017` (mapped to host)
- **Database**: `llm_benchmark` (auto-created)
- **Persistent Storage**: Data is stored in Docker volumes
- **Health Check**: Automatic health monitoring

## Docker Compose Commands

### Start Services

```bash
# Start in detached mode (background)
docker-compose up -d

# Start and view logs
docker-compose up

# Start only MongoDB
docker-compose up -d mongodb
```

### Stop Services

```bash
# Stop services (keeps containers)
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (WARNING: deletes all data)
docker-compose down -v
```

### View Logs

```bash
# View all logs
docker-compose logs

# View MongoDB logs
docker-compose logs mongodb

# Follow logs (live updates)
docker-compose logs -f mongodb

# View last 100 lines
docker-compose logs --tail=100 mongodb
```

### Check Status

```bash
# List running containers
docker-compose ps

# Show resource usage
docker-compose top
```

### Access MongoDB

```bash
# Connect to MongoDB shell
docker-compose exec mongodb mongosh

# Or using docker directly
docker exec -it llm_benchmark_mongodb mongosh

# Connect from host (if mongosh is installed locally)
mongosh mongodb://localhost:27017/llm_benchmark
```

### Data Management

```bash
# Backup MongoDB data
docker-compose exec mongodb mongodump --out /data/backup

# Restore MongoDB data
docker-compose exec mongodb mongorestore /data/backup

# View volume information
docker volume ls | grep llm_benchmark

# Remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Environment Variables

You can customize MongoDB settings by creating a `.env` file:

```env
# MongoDB connection (for your application)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=llm_benchmark

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

Or modify `docker-compose.yml` directly to add MongoDB environment variables:

```yaml
services:
  mongodb:
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: password
      MONGO_INITDB_DATABASE: llm_benchmark
```

If you set a root username/password, update your connection string:

```env
MONGODB_URL=mongodb://admin:password@localhost:27017/llm_benchmark?authSource=admin
```

## Troubleshooting

### MongoDB won't start

```bash
# Check logs
docker-compose logs mongodb

# Check if port is already in use
lsof -i :27017

# Remove and recreate container
docker-compose down
docker-compose up -d mongodb
```

### Connection refused

- Make sure MongoDB container is running: `docker-compose ps`
- Check if port 27017 is accessible: `telnet localhost 27017`
- Verify connection string in your `.env` file

### Data persistence issues

- Data is stored in Docker volumes: `docker volume ls`
- Volumes persist even after `docker-compose down`
- Use `docker-compose down -v` only if you want to delete data

### Reset everything

```bash
# Stop and remove everything including volumes
docker-compose down -v

# Remove images (optional)
docker-compose down --rmi all

# Start fresh
docker-compose up -d
```

## Optional: Run API in Docker

If you want to run the API server in Docker as well, uncomment the `api` service in `docker-compose.yml`:

```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile.api
  # ... rest of configuration
```

Then build and start:

```bash
docker-compose up -d --build
```

## Network Configuration

The services are connected via a Docker bridge network (`llm_benchmark_network`). If you run the API in Docker, it can connect to MongoDB using the service name:

```env
MONGODB_URL=mongodb://mongodb:27017
```

If running the API on the host, use:

```env
MONGODB_URL=mongodb://localhost:27017
```

## Production Considerations

For production use, consider:

1. **Security**: Set MongoDB authentication
2. **Backups**: Regular database backups
3. **Resource Limits**: Add CPU/memory limits to services
4. **Monitoring**: Add health checks and monitoring
5. **SSL/TLS**: Enable encrypted connections
6. **Replica Set**: Use MongoDB replica sets for high availability

Example production configuration:

```yaml
services:
  mongodb:
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USERNAME}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```




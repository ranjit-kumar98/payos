# Notification Service

## Purpose

This microservice is the foundation for the Notification Service in the PayOS project. It will eventually handle sending notifications via WebSocket, Email, and SMS based on Kafka events. 

**Note:** Kafka consumers, WebSocket broadcasting, Email, SMS, and business logic are not implemented in this initial chunk.

## Folder Structure

```
notification-service/
│
├── src/
│   ├── app.js               # Express app setup
│   ├── server.js            # Server startup
│   ├── config/
│   │      └── index.js      # Configuration loader
│   ├── routes/
│   │      └── health.js     # Health check route
│   └── websocket/
│          └── websocket.js  # WebSocket placeholder
│
├── package.json
├── Dockerfile
├── .dockerignore
├── .env.example
└── README.md
```

## How to Run

1. Copy `.env.example` to `.env` and adjust environment variables as needed.
2. Install dependencies:
   ```
   npm install
   ```
3. Run in development mode with auto-reload:
   ```
   npm run dev
   ```
4. Run in production mode:
   ```
   npm start
   ```
5. Alternatively, use Docker Compose to build and run the service:
   ```
   docker-compose up -d notification-service
   ```

## Available Endpoint

- `GET /health`

  Returns a JSON response indicating the service is healthy:

  ```json
  {
    "service": "notification-service",
    "status": "healthy"
  }
  ```

## Future Work

- Kafka event consumption
- WebSocket implementation
- Email sending via SendGrid
- SMS sending via Twilio
- Business logic and notification templates

These features will be implemented in later chunks.
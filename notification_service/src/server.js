const http = require('http');
const app = require('./app');
const config = require('./config');
const { initializeWebSocket } = require('./websocket/websocket');
const { startConsumer, stopConsumer } = require('./kafka/consumer');

const server = http.createServer(app);

// Initialize WebSocket (placeholder, no implementation yet)
initializeWebSocket(server);

async function startKafkaConsumer() {
  console.log('Connecting to Kafka...');
  await startConsumer();
  console.log('Connected to Kafka');
  console.log('Subscribed to payment.success');
}

startKafkaConsumer();

process.on('SIGINT', async () => {
  console.log('SIGINT received, shutting down...');
  await stopConsumer();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down...');
  await stopConsumer();
  process.exit(0);
});

server.listen(config.port, () => {
  console.log('==================================');
  console.log('Notification Service Started');
  console.log(`Port: ${config.port}`);
  console.log(`Environment: ${config.nodeEnv}`);
  console.log('==================================');
});

module.exports = server;

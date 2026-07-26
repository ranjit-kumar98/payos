const http = require('http');
const app = require('./app');
const config = require('./config');
const { initializeWebSocket } = require('./websocket/websocket');

const server = http.createServer(app);

// Initialize WebSocket (placeholder, no implementation yet)
initializeWebSocket(server);

server.listen(config.port, () => {
  console.log('==================================');
  console.log('Notification Service Started');
  console.log(`Port: ${config.port}`);
  console.log(`Environment: ${config.nodeEnv}`);
  console.log('==================================');
});

module.exports = server;
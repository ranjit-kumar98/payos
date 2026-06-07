const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 3001 });

wss.on('connection', function connection(ws) {
  console.log('Client connected');

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
    ws.send(`Echo: ${message}`);
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });

  ws.send('Welcome to PayOS Notification Service WebSocket');
});

console.log('WebSocket server running on ws://0.0.0.0:3001');
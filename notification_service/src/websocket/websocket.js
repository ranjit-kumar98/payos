const WebSocket = require('ws');

let wss;

function initializeWebSocket(server) {
  wss = new WebSocket.Server({ server, path: '/ws' });

  console.log('WebSocket Server Initialized');

  wss.on('connection', function connection(ws) {
    console.log('Client connected');

    ws.send(JSON.stringify({
      type: 'connected',
      message: 'Connected to PayOS Notification Service'
    }));

    ws.isAlive = true;

    ws.on('pong', () => {
      ws.isAlive = true;
    });

    ws.on('close', () => {
      console.log('Client disconnected');
    });
  });

  // Heartbeat interval to detect dead connections
  const interval = setInterval(() => {
    wss.clients.forEach((ws) => {
      if (ws.isAlive === false) {
        return ws.terminate();
      }

      ws.isAlive = false;
      ws.ping(() => {});
    });
  }, 30000);

  wss.on('close', () => {
    clearInterval(interval);
  });
}

function broadcast(message) {
  if (!wss) return;

  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}

module.exports = {
  initializeWebSocket,
  broadcast
};

const { startConsumer, stopConsumer } = require('./kafka/consumer');
const server = require('./server');

async function start() {
  try {
    await startConsumer();
  } catch (err) {
    console.error('Error starting Kafka consumer:', err);
  }
}

start();

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

module.exports = server;
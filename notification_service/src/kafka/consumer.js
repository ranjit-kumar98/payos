const { Kafka, logLevel } = require('kafkajs');
const config = require('../config');

const kafka = new Kafka({
  clientId: 'notification-service',
  brokers: config.kafkaBrokers,
  logLevel: logLevel.INFO,
});

const consumer = kafka.consumer({ groupId: 'payos-notification-service' });

async function startConsumer() {
  while (true) {
    try {
      await consumer.connect();
      console.log('Kafka consumer connected');

      // Subscribe to multiple topics
      await consumer.subscribe({ topic: 'payment.success', fromBeginning: false });
      await consumer.subscribe({ topic: 'payment.failed', fromBeginning: false });
      await consumer.subscribe({ topic: 'fraud.flagged', fromBeginning: false });
      await consumer.subscribe({ topic: 'fraud.detected', fromBeginning: false });

      await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
          console.log('=================================================');
          console.log('Kafka Notification Event Received');
          console.log(`Topic: ${topic}`);

          let event;

          try {
            event = JSON.parse(message.value.toString());
          } catch (err) {
            console.error('Failed to parse JSON:', err.message);
            return;
          }

          const eventType = event.event_type || 'N/A';
          console.log(`Event Type: ${eventType}`);
          console.log(`Partition: ${partition}`);
          console.log(`Offset: ${message.offset}`);

          const correlationId = event.correlation_id || 'N/A';
          const transactionId = event.payload?.transaction_id || 'N/A';
          const merchantId = event.payload?.merchant_id || 'N/A';
          const amount = event.payload?.amount || 'N/A';

          console.log(`Correlation ID: ${correlationId}`);
          console.log(`Transaction ID: ${transactionId}`);
          console.log(`Merchant ID: ${merchantId}`);
          console.log(`Amount: ${amount}`);

          console.log('Payload:');
          console.log(JSON.stringify(event, null, 3));
          console.log('=================================================');

          // Delegate to Notification Router
          const notificationRouter = require('../router/notificationRouter');
          notificationRouter.route(event);
        },
      });

      break; // Exit retry loop on successful run
    } catch (err) {
      console.error('Waiting for Kafka...', err.message);
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }
}

async function stopConsumer() {
  try {
    await consumer.disconnect();
    console.log('Kafka consumer disconnected');
  } catch (err) {
    console.error('Error disconnecting Kafka consumer:', err);
  }
}

module.exports = {
  startConsumer,
  stopConsumer,
};

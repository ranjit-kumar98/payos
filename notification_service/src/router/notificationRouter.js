const emailHandler = require('../handlers/emailHandler');
const smsHandler = require('../handlers/smsHandler');
const websocketHandler = require('../handlers/websocketHandler');

function route(event) {
  if (!event || !event.event_type) {
    console.log('Invalid event received in router');
    return;
  }

  switch (event.event_type) {
    case 'payment.success':
      console.log('Notification Router: Routing payment.success event');

      emailHandler.handlePaymentSuccess(event);
      smsHandler.handlePaymentSuccess(event);
      websocketHandler.handlePaymentSuccess(event);

      break;

    case 'payment.failed':
      console.log('Notification Router: Routing payment.failed event');

      emailHandler.handlePaymentFailed(event);
      smsHandler.handlePaymentFailed(event);
      websocketHandler.handlePaymentFailed(event);

      break;

    case 'fraud.flagged':
      console.log('Notification Router: Routing fraud.flagged event');

      emailHandler.handleFraudFlagged(event);
      smsHandler.handleFraudFlagged(event);
      websocketHandler.handleFraudFlagged(event);

      break;

    case 'fraud.detected':
      console.log('Notification Router: Routing fraud.detected event');

      emailHandler.handleFraudDetected(event);
      smsHandler.handleFraudDetected(event);
      websocketHandler.handleFraudDetected(event);

      break;

    default:
      console.log(
        `Notification Router: No handler for event type ${event.event_type}`
      );
  }
}

module.exports = {
  route,
};
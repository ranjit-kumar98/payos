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

    default:
      console.log(
        `Notification Router: No handler for event type ${event.event_type}`
      );
  }
}

module.exports = {
  route,
};
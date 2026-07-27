const websocket = require('../websocket/websocket');

async function handlePaymentSuccess(event) {
  const data = event.payload || {};

  const message = {
    type: 'payment.success',
    timestamp: new Date().toISOString(),
    data: {
      transaction_id: data.transaction_id || 'N/A',
      merchant_id: data.merchant_id || 'N/A',
      amount: data.amount || 0,
      currency: data.currency || 'N/A',
      status: 'SUCCESS',
    },
  };

  console.log('----------------------------------');
  console.log('[WEBSOCKET]');
  console.log('Broadcasting payment.success event');
  websocket.broadcast(JSON.stringify(message));
  console.log('----------------------------------');
}

module.exports = {
  handlePaymentSuccess,
};

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

async function handlePaymentFailed(event) {
  const data = event.payload || {};

  const message = {
    type: 'payment.failed',
    timestamp: event.timestamp || new Date().toISOString(),
    data: {
      transaction_id: data.transaction_id || 'N/A',
      merchant_id: data.merchant_id || 'N/A',
      amount: data.amount || 0,
      currency: data.currency || 'N/A',
      payment_method: data.payment_method || 'N/A',
      status: data.status || 'FAILED',
      decline_reason: data.decline_reason || 'N/A',
    },
  };

  console.log('----------------------------------');
  console.log('[WEBSOCKET]');
  console.log('Broadcasting payment.failed event');
  websocket.broadcast(JSON.stringify(message));
  console.log('----------------------------------');
}

async function handleFraudFlagged(event) {
  const data = event.payload || {};

  const message = {
    type: 'fraud.flagged',
    priority: 'WARNING',
    timestamp: event.timestamp || new Date().toISOString(),
    data: {
      transaction_id: data.transaction_id || 'N/A',
      merchant_id: data.merchant_id || 'N/A',
      amount: data.amount || 0,
      currency: data.currency || 'N/A',
      payment_method: data.payment_method || 'N/A',
      status: data.status || 'N/A',
      risk_score: data.risk_score || 'N/A',
      risk_tier: data.risk_tier || 'N/A',
      triggered_rules: data.triggered_rules || [],
    },
  };

  console.log('----------------------------------');
  console.log('[WEBSOCKET]');
  console.log('Broadcasting fraud.flagged event');
  websocket.broadcast(JSON.stringify(message));
  console.log('----------------------------------');
}

async function handleFraudDetected(event) {
  const data = event.payload || {};

  const message = {
    type: 'fraud.detected',
    priority: 'URGENT',
    timestamp: event.timestamp || new Date().toISOString(),
    data: {
      transaction_id: data.transaction_id || 'N/A',
      merchant_id: data.merchant_id || 'N/A',
      amount: data.amount || 0,
      currency: data.currency || 'N/A',
      payment_method: data.payment_method || 'N/A',
      status: data.status || 'N/A',
      risk_score: data.risk_score || 'N/A',
      risk_tier: data.risk_tier || 'N/A',
      triggered_rules: data.triggered_rules || [],
    },
  };

  console.log('----------------------------------');
  console.log('[WEBSOCKET]');
  console.log('Broadcasting fraud.detected event');
  websocket.broadcast(JSON.stringify(message));
  console.log('----------------------------------');
}

module.exports = {
  handlePaymentSuccess,
  handlePaymentFailed,
  handleFraudFlagged,
  handleFraudDetected,
};

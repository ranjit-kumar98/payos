const smsService = require('../services/smsService');
const config = require('../config');

async function handlePaymentSuccess(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[SMS]');
  console.log('Preparing SMS notification...');

  const transactionId = data.transaction_id || 'N/A';
  const merchantId = data.merchant_id || 'N/A';
  const amount = data.amount || 'N/A';

  const message = `
PayOS

Payment Successful

Amount: ₹${amount}

Transaction ID:
${transactionId}

Thank you for using PayOS.
  `;

  try {
    await smsService.sendSms(config.testPhoneNumber, message);
  } catch (error) {
    console.error('SMS delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handlePaymentFailed(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[SMS]');
  console.log('Preparing payment.failed SMS notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const declineReason = data.decline_reason || 'N/A';

  const message = `
PayOS: Payment of ₹${amount} failed.
Reason: ${declineReason}
Transaction: ${transactionId}
  `;

  try {
    await smsService.sendSms(config.testPhoneNumber, message);
  } catch (error) {
    console.error('SMS delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handleFraudFlagged(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[SMS]');
  console.log('Preparing fraud.flagged SMS notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const riskScore = data.risk_score || 'N/A';
  const riskTier = data.risk_tier || 'N/A';

  const message = `
PayOS Alert: Transaction flagged for review.
Amount: ₹${amount}
Risk: ${riskTier} (${riskScore})
Transaction: ${transactionId}
  `;

  try {
    await smsService.sendSms(config.testPhoneNumber, message);
  } catch (error) {
    console.error('SMS delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handleFraudDetected(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[SMS]');
  console.log('Preparing fraud.detected SMS notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const riskScore = data.risk_score || 'N/A';
  const riskTier = data.risk_tier || 'N/A';

  const message = `
PayOS FRAUD ALERT: High fraud risk detected.
Amount: ₹${amount}
Risk: ${riskTier} (${riskScore})
Transaction: ${transactionId}
  `;

  try {
    await smsService.sendSms(config.testPhoneNumber, message);
  } catch (error) {
    console.error('SMS delivery failed:', error);
  }

  console.log('----------------------------------');
}

module.exports = {
  handlePaymentSuccess,
  handlePaymentFailed,
  handleFraudFlagged,
  handleFraudDetected,
};
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

module.exports = {
  handlePaymentSuccess,
};

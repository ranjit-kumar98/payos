const emailService = require('../services/emailService');
const config = require('../config');

async function handlePaymentSuccess(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[EMAIL]');
  console.log('Preparing email notification...');

  const transactionId = data.transaction_id || 'N/A';
  const merchantId = data.merchant_id || 'N/A';
  const amount = data.amount || 'N/A';
  const currency = data.currency || 'N/A';
  const paymentMethod = data.payment_method || 'N/A';
  const timestamp = event.timestamp || new Date().toISOString();

  const subject = 'Payment Successful - PayOS';

  const html = `
    <div style="font-family: Arial, sans-serif; border: 1px solid #ccc; padding: 20px;">
      <h2>PayOS</h2>
      <h3>Payment Successful</h3>
      <p>Your payment has been processed successfully.</p>
      <p><strong>Transaction ID:</strong> ${transactionId}</p>
      <p><strong>Merchant ID:</strong> ${merchantId}</p>
      <p><strong>Amount:</strong> ₹${amount}</p>
      <p><strong>Currency:</strong> ${currency}</p>
      <p><strong>Payment Method:</strong> ${paymentMethod}</p>
      <p><strong>Status:</strong> SUCCESS</p>
      <p><strong>Date:</strong> ${timestamp}</p>
      <p>Thank you for choosing PayOS.</p>
      <p><em>This is an automated email.</em></p>
    </div>
  `;

  try {
    await emailService.sendEmail(config.testEmail, subject, html);
  } catch (error) {
    console.error('Email delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handlePaymentFailed(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[EMAIL]');
  console.log('Preparing payment.failed email notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const currency = data.currency || 'N/A';
  const paymentMethod = data.payment_method || 'N/A';
  const status = data.status || 'FAILED';
  const declineReason = data.decline_reason || 'N/A';
  const timestamp = event.timestamp || new Date().toISOString();

  const subject = 'Payment Failed - PayOS';

  const html = `
    <div style="font-family: Arial, sans-serif; border: 1px solid #ccc; padding: 20px;">
      <h2>PayOS</h2>
      <h3>Payment Failed</h3>
      <p>Your payment has failed.</p>
      <p><strong>Transaction ID:</strong> ${transactionId}</p>
      <p><strong>Amount:</strong> ₹${amount}</p>
      <p><strong>Currency:</strong> ${currency}</p>
      <p><strong>Payment Method:</strong> ${paymentMethod}</p>
      <p><strong>Status:</strong> ${status}</p>
      <p><strong>Decline Reason:</strong> ${declineReason}</p>
      <p><strong>Date:</strong> ${timestamp}</p>
      <p>Please try again or contact support.</p>
      <p><em>This is an automated email.</em></p>
    </div>
  `;

  try {
    await emailService.sendEmail(config.testEmail, subject, html);
  } catch (error) {
    console.error('Email delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handleFraudFlagged(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[EMAIL]');
  console.log('Preparing fraud.flagged email notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const currency = data.currency || 'N/A';
  const paymentMethod = data.payment_method || 'N/A';
  const riskScore = data.risk_score || 'N/A';
  const riskTier = data.risk_tier || 'N/A';
  const triggeredRules = data.triggered_rules || [];
  const status = data.status || 'N/A';
  const timestamp = event.timestamp || new Date().toISOString();

  const subject = 'Payment Flagged for Review - PayOS';

  const html = `
    <div style="font-family: Arial, sans-serif; border: 1px solid #ccc; padding: 20px;">
      <h2>PayOS</h2>
      <h3>Payment Flagged for Review</h3>
      <p>Your payment has been flagged for review.</p>
      <p><strong>Transaction ID:</strong> ${transactionId}</p>
      <p><strong>Amount:</strong> ₹${amount}</p>
      <p><strong>Currency:</strong> ${currency}</p>
      <p><strong>Payment Method:</strong> ${paymentMethod}</p>
      <p><strong>Risk Score:</strong> ${riskScore}</p>
      <p><strong>Risk Tier:</strong> ${riskTier}</p>
      <p><strong>Triggered Rules:</strong> ${triggeredRules.join(', ')}</p>
      <p><strong>Status:</strong> ${status}</p>
      <p><strong>Date:</strong> ${timestamp}</p>
      <p>Please review the transaction.</p>
      <p><em>This is an automated email.</em></p>
    </div>
  `;

  try {
    await emailService.sendEmail(config.testEmail, subject, html);
  } catch (error) {
    console.error('Email delivery failed:', error);
  }

  console.log('----------------------------------');
}

async function handleFraudDetected(event) {
  const data = event.payload || {};

  console.log('----------------------------------');
  console.log('[EMAIL]');
  console.log('Preparing fraud.detected email notification...');

  const transactionId = data.transaction_id || 'N/A';
  const amount = data.amount || 'N/A';
  const currency = data.currency || 'N/A';
  const paymentMethod = data.payment_method || 'N/A';
  const riskScore = data.risk_score || 'N/A';
  const riskTier = data.risk_tier || 'N/A';
  const triggeredRules = data.triggered_rules || [];
  const status = data.status || 'N/A';
  const timestamp = event.timestamp || new Date().toISOString();

  const subject = 'URGENT: Fraud Risk Detected - PayOS';

  const html = `
    <div style="font-family: Arial, sans-serif; border: 1px solid #ccc; padding: 20px;">
      <h2>PayOS</h2>
      <h3>URGENT: Fraud Risk Detected</h3>
      <p>A high fraud risk has been detected for a transaction.</p>
      <p><strong>Transaction ID:</strong> ${transactionId}</p>
      <p><strong>Amount:</strong> ₹${amount}</p>
      <p><strong>Currency:</strong> ${currency}</p>
      <p><strong>Payment Method:</strong> ${paymentMethod}</p>
      <p><strong>Risk Score:</strong> ${riskScore}</p>
      <p><strong>Risk Tier:</strong> ${riskTier}</p>
      <p><strong>Triggered Rules:</strong> ${triggeredRules.join(', ')}</p>
      <p><strong>Status:</strong> ${status}</p>
      <p><strong>Date:</strong> ${timestamp}</p>
      <p>Please investigate immediately.</p>
      <p><em>This is an automated email.</em></p>
    </div>
  `;

  try {
    await emailService.sendEmail(config.testEmail, subject, html);
  } catch (error) {
    console.error('Email delivery failed:', error);
  }

  console.log('----------------------------------');
}

module.exports = {
  handlePaymentSuccess,
  handlePaymentFailed,
  handleFraudFlagged,
  handleFraudDetected,
};



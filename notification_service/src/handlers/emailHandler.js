function handlePaymentSuccess(event) {
  const data = event.payload || {};
  console.log('----------------------------------');
  console.log('[EMAIL]');
  console.log('Preparing email notification');
  console.log('Transaction:', data.transaction_id || 'N/A');
  console.log('Merchant:', data.merchant_id || 'N/A');
  console.log('Amount:', data.amount || 'N/A');
  console.log('----------------------------------');
}


module.exports = {
  handlePaymentSuccess,
};
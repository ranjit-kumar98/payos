const twilio = require('twilio');
const config = require('../config');

const client = twilio(config.twilioAccountSid, config.twilioAuthToken);

async function sendSms(to, body) {
  try {
    console.log('[SMS]');
    console.log('Preparing SMS notification...');
    console.log('Sending SMS via Twilio...');

    const message = await client.messages.create({
      body,
      from: config.twilioPhoneNumber,
      to,
    });

    console.log('SMS delivered successfully.');
    console.log('Message SID:', message.sid);
    return message;
  } catch (error) {
    console.error('Error sending SMS:', error);
    throw error;
  }
}

module.exports = {
  sendSms,
};
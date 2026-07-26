const dotenv = require('dotenv');

dotenv.config();

const requiredEnvVars = [
  'PORT',
  'NODE_ENV',
  'KAFKA_BROKERS',
  'TWILIO_ACCOUNT_SID',
  'TWILIO_AUTH_TOKEN',
  'TWILIO_PHONE_NUMBER',
  'TEST_PHONE_NUMBER'
];

for (const varName of requiredEnvVars) {
  if (!process.env[varName]) {
    console.error(`Missing required environment variable: ${varName}`);
    process.exit(1);
  }
}

module.exports = {
  port: parseInt(process.env.PORT, 10),
  nodeEnv: process.env.NODE_ENV,
  kafkaBrokers: process.env.KAFKA_BROKERS.split(',').map(broker => broker.trim()),
  twilioAccountSid: process.env.TWILIO_ACCOUNT_SID,
  twilioAuthToken: process.env.TWILIO_AUTH_TOKEN,
  twilioPhoneNumber: process.env.TWILIO_PHONE_NUMBER,
  testPhoneNumber: process.env.TEST_PHONE_NUMBER
};

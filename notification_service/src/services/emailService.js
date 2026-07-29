const sgMail = require('@sendgrid/mail');
const config = require('../config');

sgMail.setApiKey(config.sendgridApiKey);

async function sendEmail(to, subject, html) {
  try {
    console.log('[EMAIL]');
    console.log('Preparing email notification...');
    console.log('Sending email via SendGrid...');

    const msg = {
      to,
      from: config.sendgridFromEmail,
      subject,
      html,
    };

    const response = await sgMail.send(msg);

    console.log('Email delivered successfully.');
    console.log('Recipient:', to);
    console.log('Transaction:', subject);
    return response;
  } catch (error) {
    console.error('Error sending email:', error);
    throw error;
  }
}

module.exports = {
  sendEmail,
};
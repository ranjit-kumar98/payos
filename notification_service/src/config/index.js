const dotenv = require('dotenv');

dotenv.config();

const requiredEnvVars = ['PORT', 'NODE_ENV'];

for (const varName of requiredEnvVars) {
  if (!process.env[varName]) {
    console.error(`Missing required environment variable: ${varName}`);
    process.exit(1);
  }
}

module.exports = {
  port: parseInt(process.env.PORT, 10),
  nodeEnv: process.env.NODE_ENV
};
const express = require('express');
const healthRouter = require('./routes/health');
const config = require('./config');

const app = express();

app.use(express.json());

app.use('/health', healthRouter);

module.exports = app;
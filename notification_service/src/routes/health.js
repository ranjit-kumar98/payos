const express = require('express');
const router = express.Router();

router.get('/', (req, res) => {
  res.json({
    service: 'notification_service',
    status: 'healthy'
  });
});

module.exports = router;
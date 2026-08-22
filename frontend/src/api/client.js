import axios from 'axios';

const configuredApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Backend analytics routes are exposed under /api.
// Avoid adding /api twice if the environment variable already contains it.
const baseURL = configuredApiUrl.replace(/\/+$/, '').endsWith('/api')
  ? configuredApiUrl.replace(/\/+$/, '')
  : `${configuredApiUrl.replace(/\/+$/, '')}/api`;

const apiClient = axios.create({
  baseURL,
  headers: {
    Accept: 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Dashboard API functions

export function getAnalyticsOverview(days) {
  return apiClient.get('/analytics/overview', {
    params: { days },
  });
}

export function getDailyGMVTrend(days) {
  return apiClient.get('/analytics/daily-gmv-trend', {
    params: { days },
  });
}

export function getPaymentMethodBreakdown(days) {
  return apiClient.get('/analytics/payment-method-breakdown', {
    params: { days },
  });
}

export function getTopMerchants(days) {
  return apiClient.get('/analytics/top-merchants', {
    params: { days },
  });
}

export function getBnplLoans() {
  return apiClient.get('/bnpl/loans').then(res => res.data);
}

export async function getTransactions(params) {
  // params: { status, payment_method, merchant_id, start_date, end_date, page, page_size }
  const response = await apiClient.get('/transactions/', { params });
  return response.data;
}

export async function getTransaction(transactionId) {
  const response = await apiClient.get(`/transactions/${transactionId}`);
  return response.data;
}

export function getFraudReports() {
  return apiClient.get('/fraud-reports').then(res => res.data);
}

export function getFraudHeatmap(days) {
  return apiClient.get(`/analytics/fraud-heatmap?days=${days}`).then(res => res.data);
}

export function getHighRiskTransactions(page, size) {
  return apiClient.get(`/fraud/high-risk?page=${page}&size=${size}`).then(res => res.data);
}

// BNPL API functions

export function checkBnplEligibility(principal, tenure) {
  return apiClient.post('/bnpl/eligibility', {
    principal,
    tenure,
  }).then(res => res.data);
}

export function calculateBnpl(principal, tenure) {
  return apiClient.post('/bnpl/calculate', {
    principal,
    tenure,
  }).then(res => res.data);
}

export function createBnplLoan(principal, tenure) {
  return apiClient.post('/bnpl/loans', {
    principal,
    tenure,
  }).then(res => res.data);
}

  
// Payment API functions for Checkout Demo

export function routePayment(amount, currency, paymentMethod) {
  return apiClient.post('/payments/route', {
    amount,
    currency,
    payment_method: paymentMethod,
  }).then(res => res.data);
}

export function createPaymentOrder(amount, currency, paymentMethod) {
  return apiClient.post('/payments/create-order', {
    amount,
    currency,
    payment_method: paymentMethod,
  }).then(res => res.data);
}

// Disputes API functions

export function getDisputes(params) {
  return apiClient.get('/disputes', { params });
}

export function getDispute(disputeId) {
  return apiClient.get(`/disputes/${disputeId}`);
}

export function moveDisputeToReview(disputeId) {
  return apiClient.post(`/disputes/${disputeId}/review`);
}

export function resolveDispute(disputeId, resolutionNotes) {
  return apiClient.post(`/disputes/${disputeId}/resolve`, null, {
    params: { resolution_notes: resolutionNotes },
  });
}

export function rejectDispute(disputeId, resolutionNotes) {
  return apiClient.post(`/disputes/${disputeId}/reject`, null, {
    params: { resolution_notes: resolutionNotes },
  });
}

export default apiClient;

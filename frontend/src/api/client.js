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
  return apiClient.get('/bnpl/loans');
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

// Fraud Monitor API functions

export function getFraudReports() {
  return apiClient.get('/fraud-reports').then(res => res.data);
}

export function getFraudHeatmap(days) {
  return apiClient.get(`/analytics/fraud-heatmap?days=${days}`).then(res => res.data);
}

export function getHighRiskTransactions(page, size) {
  return apiClient.get(`/fraud/high-risk?page=${page}&size=${size}`).then(res => res.data);
}

export default apiClient;

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  getFraudReports,
  getFraudHeatmap,
  getHighRiskTransactions,
} from '../api/client';
import { formatIndianCurrency, formatDateTimeIST } from '../utils/formatters';

const PAGE_SIZE = 50;
const REFRESH_INTERVAL = 30000;

function unwrapResponse(response) {
  // Supports both:
  // 1. API functions returning response.data
  // 2. API functions returning the full Axios response
  if (response && typeof response === 'object' && 'data' in response) {
    return response.data;
  }

  return response;
}

function formatRiskTier(tier) {
  if (!tier) return 'UNKNOWN';

  return String(tier)
    .replace(/_/g, ' ')
    .toUpperCase();
}

function getStatusClasses(status) {
  const normalized = String(status || '').toUpperCase();

  switch (normalized) {
    case 'SUCCESS':
      return 'bg-green-100 text-green-700 border border-green-200';

    case 'FAILED':
      return 'bg-red-100 text-red-700 border border-red-200';

    case 'PENDING':
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200';

    case 'REFUNDED':
      return 'bg-blue-100 text-blue-700 border border-blue-200';

    case 'BLOCKED':
      return 'bg-red-100 text-red-800 border border-red-300';

    default:
      return 'bg-gray-100 text-gray-700 border border-gray-200';
  }
}

function getRiskClasses(tier) {
  const normalized = String(tier || '').toUpperCase();

  if (normalized === 'HIGH') {
    return 'bg-red-100 text-red-700 border border-red-200';
  }

  if (normalized === 'MEDIUM') {
    return 'bg-yellow-100 text-yellow-800 border border-yellow-200';
  }

  return 'bg-green-100 text-green-700 border border-green-200';
}

function getHeatmapClasses(count, maxCount) {
  if (count === 0) {
    return 'bg-gray-100 border-gray-200';
  }

  if (maxCount <= 1) {
    return 'bg-red-500 border-red-600';
  }

  const intensity = count / maxCount;

  if (intensity <= 0.2) {
    return 'bg-red-100 border-red-200';
  }

  if (intensity <= 0.4) {
    return 'bg-red-200 border-red-300';
  }

  if (intensity <= 0.6) {
    return 'bg-red-300 border-red-400';
  }

  if (intensity <= 0.8) {
    return 'bg-red-400 border-red-500';
  }

  return 'bg-red-600 border-red-700';
}

function formatHour(hour) {
  const numericHour = Number(hour);

  if (Number.isNaN(numericHour)) {
    return '--';
  }

  const suffix = numericHour >= 12 ? 'PM' : 'AM';
  const hour12 = numericHour % 12 === 0 ? 12 : numericHour % 12;

  return `${hour12} ${suffix}`;
}

function FraudMonitor() {
  const [fraudReport, setFraudReport] = useState(null);
  const [heatmapData, setHeatmapData] = useState([]);
  const [highRiskData, setHighRiskData] = useState({
    total: 0,
    page: 1,
    size: PAGE_SIZE,
    items: [],
  });

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchingRef = useRef(false);
  const mountedRef = useRef(true);

  const fetchAllData = useCallback(async (isInitial = false) => {
    if (fetchingRef.current) {
      return;
    }

    fetchingRef.current = true;

    if (isInitial) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }

    setError(null);

    try {
      const [fraudReportsResponse, heatmapResponse, highRiskResponse] =
        await Promise.all([
          getFraudReports(),
          getFraudHeatmap(1),
          getHighRiskTransactions(1, PAGE_SIZE),
        ]);

      if (!mountedRef.current) {
        return;
      }

      /*
       * FRAUD REPORTS
       *
       * Actual backend response:
       * [
       *   {
       *     report_date,
       *     blocked_transactions,
       *     blocked_amount,
       *     top_triggered_rules
       *   }
       * ]
       */
      const fraudReports = unwrapResponse(fraudReportsResponse);

      if (Array.isArray(fraudReports) && fraudReports.length > 0) {
        const sortedReports = [...fraudReports].sort(
          (a, b) =>
            new Date(b.report_date || b.created_at || 0) -
            new Date(a.report_date || a.created_at || 0)
        );

        setFraudReport(sortedReports[0]);
      } else {
        setFraudReport(null);
      }

      /*
       * HEATMAP
       *
       * Actual backend response is an array of 24 objects.
       */
      const heatmap = unwrapResponse(heatmapResponse);

      if (Array.isArray(heatmap)) {
        const normalizedHeatmap = Array.from({ length: 24 }, (_, hour) => {
          const item = heatmap.find(
            (entry) => Number(entry?.hour) === hour
          );

          return {
            hour,
            low_risk_count: Number(item?.low_risk_count || 0),
            medium_risk_count: Number(item?.medium_risk_count || 0),
            high_risk_count: Number(item?.high_risk_count || 0),
          };
        });

        setHeatmapData(normalizedHeatmap);
      } else {
        setHeatmapData([]);
      }

      /*
       * HIGH-RISK TRANSACTIONS
       *
       * Actual backend response:
       * {
       *   total,
       *   page,
       *   size,
       *   items: []
       * }
       */
      const highRisk = unwrapResponse(highRiskResponse);

      if (highRisk && typeof highRisk === 'object') {
        setHighRiskData({
          total: Number(highRisk.total || 0),
          page: Number(highRisk.page || 1),
          size: Number(highRisk.size || PAGE_SIZE),
          items: Array.isArray(highRisk.items) ? highRisk.items : [],
        });
      } else {
        setHighRiskData({
          total: 0,
          page: 1,
          size: PAGE_SIZE,
          items: [],
        });
      }
    } catch (err) {
      console.error('Fraud Monitor fetch failed:', err);

      if (mountedRef.current) {
        setError(
          err?.response?.data?.detail ||
            err?.message ||
            'Failed to load Fraud Monitor data.'
        );
      }
    } finally {
      fetchingRef.current = false;

      if (mountedRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    fetchAllData(true);

    const intervalId = window.setInterval(() => {
      fetchAllData(false);
    }, REFRESH_INTERVAL);

    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [fetchAllData]);

  const blockedTransactions =
    Number(fraudReport?.blocked_transactions) || 0;

  const blockedAmount =
    Number(fraudReport?.blocked_amount) || 0;

  const topRule =
    Array.isArray(fraudReport?.top_triggered_rules) &&
    fraudReport.top_triggered_rules.length > 0
      ? fraudReport.top_triggered_rules[0]
      : 'No triggered rules';

  const maxHeatmapCount = heatmapData.reduce((max, item) => {
    const total =
      Number(item.low_risk_count || 0) +
      Number(item.medium_risk_count || 0) +
      Number(item.high_risk_count || 0);

    return Math.max(max, total);
  }, 0);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-semibold text-gray-900">
            Fraud Monitor
          </h1>

          {fraudReport?.report_date && (
            <p className="text-sm text-gray-500 mt-1">
              Latest report: {fraudReport.report_date}
            </p>
          )}
        </div>

        {refreshing && (
          <span className="text-xs text-gray-500">
            Refreshing...
          </span>
        )}
      </div>

      {/* Global Error */}
      {error && (
        <div className="mb-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
        {/* Blocked Transactions */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <p className="text-sm font-medium text-gray-500">
            Blocked Transactions
          </p>

          {loading ? (
            <div className="mt-3 h-8 w-24 bg-gray-200 rounded animate-pulse" />
          ) : (
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {blockedTransactions.toLocaleString('en-IN')}
            </p>
          )}
        </div>

        {/* Amount at Risk */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <p className="text-sm font-medium text-gray-500">
            Amount at Risk
          </p>

          {loading ? (
            <div className="mt-3 h-8 w-36 bg-gray-200 rounded animate-pulse" />
          ) : (
            <p className="mt-2 text-3xl font-bold text-gray-900">
              {formatIndianCurrency(blockedAmount)}
            </p>
          )}
        </div>

        {/* Top Rule */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <p className="text-sm font-medium text-gray-500">
            Top Rule
          </p>

          {loading ? (
            <div className="mt-3 h-8 w-40 bg-gray-200 rounded animate-pulse" />
          ) : (
            <p className="mt-2 text-lg font-semibold text-gray-900">
              {topRule}
            </p>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.6fr)_minmax(360px,0.9fr)] gap-6">
        {/* Heatmap */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                24-Hour Fraud/Risk Activity
              </h2>

              <p className="text-sm text-gray-500 mt-1">
                Risk activity by hour for the last 24 hours
              </p>
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-2">
              {Array.from({ length: 24 }).map((_, index) => (
                <div
                  key={index}
                  className="h-14 rounded-md bg-gray-200 animate-pulse"
                />
              ))}
            </div>
          ) : heatmapData.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              No heatmap data available.
            </div>
          ) : (
            <>
              <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-2">
                {heatmapData.map((item) => {
                  const low = Number(item.low_risk_count || 0);
                  const medium = Number(item.medium_risk_count || 0);
                  const high = Number(item.high_risk_count || 0);
                  const total = low + medium + high;

                  return (
                    <div key={item.hour}>
                      <div
                        className={`h-14 rounded-md border ${getHeatmapClasses(
                          total,
                          maxHeatmapCount
                        )} flex items-center justify-center cursor-default`}
                        title={`${formatHour(item.hour)}
Low Risk: ${low}
Medium Risk: ${medium}
High Risk: ${high}
Total: ${total}`}
                      >
                        <span
                          className={`text-sm font-semibold ${
                            total > 0
                              ? 'text-gray-900'
                              : 'text-gray-400'
                          }`}
                        >
                          {total}
                        </span>
                      </div>

                      <div className="text-center text-xs text-gray-500 mt-1">
                        {formatHour(item.hour)}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Legend */}
              <div className="flex flex-wrap gap-5 mt-6 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-gray-100 border border-gray-200" />
                  No activity
                </div>

                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-red-100" />
                  Low
                </div>

                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-red-300" />
                  Medium
                </div>

                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 rounded bg-red-600" />
                  High
                </div>
              </div>
            </>
          )}
        </section>

        {/* High-Risk Transactions */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200 p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                High-Risk Transactions
              </h2>

              <p className="text-sm text-gray-500 mt-1">
                {highRiskData.total.toLocaleString('en-IN')} transaction
                {highRiskData.total === 1 ? '' : 's'}
              </p>
            </div>
          </div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, index) => (
                <div
                  key={index}
                  className="h-28 rounded-md bg-gray-100 animate-pulse"
                />
              ))}
            </div>
          ) : highRiskData.items.length === 0 ? (
            <div className="py-12 text-center">
              <div className="text-4xl mb-3">🛡️</div>
              <p className="font-medium text-gray-700">
                No high-risk transactions found
              </p>
              <p className="text-sm text-gray-500 mt-1">
                There are currently no transactions in the high-risk queue.
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[650px] overflow-y-auto pr-1">
              {highRiskData.items.map((tx) => {
                const riskScore = Number(tx.risk_score || 0);
                const riskTier = formatRiskTier(tx.risk_tier);

                return (
                  <div
                    key={tx.transaction_id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 hover:shadow-sm transition"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p
                          className="text-sm font-semibold text-gray-900 truncate"
                          title={tx.merchant_id || ''}
                        >
                          Merchant
                        </p>

                        <p
                          className="text-xs text-gray-500 truncate"
                          title={tx.merchant_id || ''}
                        >
                          {tx.merchant_id || 'N/A'}
                        </p>
                      </div>

                      <span
                        className={`shrink-0 px-2 py-1 rounded-full text-xs font-semibold ${getRiskClasses(
                          riskTier
                        )}`}
                      >
                        {riskTier} · {riskScore}
                      </span>
                    </div>

                    <div className="flex items-center justify-between mt-4">
                      <p className="text-lg font-bold text-gray-900">
                        {tx.currency || 'INR'}{' '}
                        {Number(tx.amount || 0).toLocaleString('en-IN', {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>

                      <span
                        className={`px-2 py-1 rounded-full text-xs font-semibold ${getStatusClasses(
                          tx.status
                        )}`}
                      >
                        {String(tx.status || 'UNKNOWN').toUpperCase()}
                      </span>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-2">
                      {Array.isArray(tx.triggered_rules) &&
                      tx.triggered_rules.length > 0 ? (
                        tx.triggered_rules.map((rule, index) => (
                          <span
                            key={`${tx.transaction_id}-rule-${index}`}
                            className="px-2 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-medium"
                          >
                            {rule}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-gray-400 italic">
                          No triggered rules
                        </span>
                      )}
                    </div>

                    <div className="mt-3 pt-3 border-t border-gray-100 text-xs text-gray-500 space-y-1">
                      <p>
                        Payment Method:{' '}
                        <span className="font-medium text-gray-700">
                          {tx.payment_method || 'N/A'}
                        </span>
                      </p>

                      <p>
                        Created:{' '}
                        {tx.created_at
                          ? formatDateTimeIST(tx.created_at)
                          : 'N/A'}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default FraudMonitor;
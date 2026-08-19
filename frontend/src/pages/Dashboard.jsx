import React, { useEffect, useRef, useState } from 'react';
import { KPICard } from '../components/KPICard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ToastProvider, useToast } from '../components/ToastProvider';
import { useWebSocket } from '../hooks/useWebSocket';

import {
  getAnalyticsOverview,
  getDailyGMVTrend,
  getPaymentMethodBreakdown,
  getTopMerchants,
  getBnplLoans,
} from '../api/client';

import { formatIndianCurrency } from '../utils/formatters';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
  Legend,
  CartesianGrid,
} from 'recharts';

const PERIODS = [
  { label: '7D', days: 7 },
  { label: '30D', days: 30 },
  { label: '90D', days: 90 },
];

const PAYMENT_METHOD_COLORS = {
  UPI: '#3b82f6',
  CARD: '#8b5cf6',
  Card: '#8b5cf6',
  WALLET: '#22c55e',
  Wallet: '#22c55e',
  NETBANKING: '#f97316',
  Netbanking: '#f97316',
  'NET BANKING': '#f97316',
};

function formatPercentage(value) {
  if (
    value === undefined ||
    value === null ||
    Number.isNaN(Number(value))
  ) {
    return 'N/A';
  }

  return `${Number(value).toFixed(2)}%`;
}

function getPaymentMethodColor(method) {
  return PAYMENT_METHOD_COLORS[method] || '#3b82f6';
}

function DashboardContent() {
  const [period, setPeriod] = useState(30);

  const [overview, setOverview] = useState(null);
  const [gmvTrend, setGmvTrend] = useState([]);
  const [paymentMethodBreakdown, setPaymentMethodBreakdown] = useState([]);
  const [topMerchants, setTopMerchants] = useState([]);
  const [activeBnplLoans, setActiveBnplLoans] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const toast = useToast();

  // Prevent older API requests from overwriting newer period data.
  const requestIdRef = useRef(0);

  useEffect(() => {
    const requestId = ++requestIdRef.current;

    setLoading(true);
    setError('');

    /*
     * ------------------------------------------------------------
     * MAIN DASHBOARD ANALYTICS
     * ------------------------------------------------------------
     *
     * BNPL is intentionally NOT included here.
     * If BNPL fails, the rest of the dashboard must still work.
     */
    Promise.all([
      getAnalyticsOverview(period),
      getDailyGMVTrend(period),
      getPaymentMethodBreakdown(period),
      getTopMerchants(period),
    ])
      .then(
        ([
          overviewRes,
          gmvTrendRes,
          paymentMethodRes,
          topMerchantsRes,
        ]) => {
          if (requestId !== requestIdRef.current) {
            return;
          }

          const overviewData = overviewRes?.data;
          const gmvData = gmvTrendRes?.data;
          const paymentData = paymentMethodRes?.data;
          const merchantData = topMerchantsRes?.data;

          setOverview(
            overviewData && typeof overviewData === 'object'
              ? overviewData
              : null
          );

          setGmvTrend(Array.isArray(gmvData) ? gmvData : []);

          setPaymentMethodBreakdown(
            Array.isArray(paymentData) ? paymentData : []
          );

          setTopMerchants(
            Array.isArray(merchantData) ? merchantData : []
          );
        }
      )
      .catch((err) => {
        if (requestId !== requestIdRef.current) {
          return;
        }

        console.error('Dashboard analytics API error:', err);

        setOverview(null);
        setGmvTrend([]);
        setPaymentMethodBreakdown([]);
        setTopMerchants([]);

        setError('Failed to load dashboard data.');
      })
      .finally(() => {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      });

    /*
     * ------------------------------------------------------------
     * BNPL
     * ------------------------------------------------------------
     *
     * This is intentionally a separate request.
     *
     * getBnplLoans() uses the existing Axios client, which points
     * to:
     *
     * http://localhost:8000/api
     *
     * The endpoint returns all loans for the current user.
     * Therefore we count only ACTIVE loans.
     *
     * A BNPL failure must NOT break the dashboard.
     */
    getBnplLoans()
      .then((bnplResponse) => {
        if (requestId !== requestIdRef.current) {
          return;
        }

        const loans = bnplResponse?.data;

        console.log('Dashboard BNPL loans response:', loans);

        if (!Array.isArray(loans)) {
          setActiveBnplLoans(null);
          return;
        }

        const activeCount = loans.filter(
          (loan) => loan?.status === 'ACTIVE'
        ).length;

        console.log('Active BNPL loan count:', activeCount);

        setActiveBnplLoans(activeCount);
      })
      .catch((err) => {
        if (requestId !== requestIdRef.current) {
          return;
        }

        console.error('Failed to fetch BNPL loans:', err);

        // BNPL failure should not break the dashboard.
        setActiveBnplLoans(null);
      });
  }, [period]);

  /*
   * ------------------------------------------------------------
   * WEBSOCKET PAYMENT SUCCESS
   * ------------------------------------------------------------
   */
  useWebSocket({
    onPaymentSuccess: (data) => {
      const amount = Number(data?.data?.amount || 0);

      if (!amount) {
        return;
      }

      setOverview((prev) => {
        if (!prev) {
          return prev;
        }

        return {
          ...prev,
          total_successful_volume:
            Number(prev.total_successful_volume || 0) + amount,
        };
      });

      toast.addToast({
        type: 'success',
        message: `New payment: ₹${formatIndianCurrency(amount)} from ${
          data?.data?.merchant_id || 'unknown'
        }`,
      });
    },
  });

  if (error) {
    return (
      <div className="p-4 text-red-600">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* =========================================================
          KPI CARDS
          ========================================================= */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {loading || !overview ? (
          <>
            <LoadingSpinner />
            <LoadingSpinner />
            <LoadingSpinner />
            <LoadingSpinner />
          </>
        ) : (
          <>
            <KPICard
              title="Total GMV"
              value={
                overview.total_successful_volume !== undefined &&
                overview.total_successful_volume !== null
                  ? formatIndianCurrency(
                      overview.total_successful_volume
                    )
                  : 'N/A'
              }
            />

            <KPICard
              title="Success Rate"
              value={formatPercentage(overview.success_rate)}
            />

            <KPICard
              title="Fraud Blocked"
              value={
                overview.blocked_transactions !== undefined &&
                overview.blocked_transactions !== null
                  ? `${overview.blocked_transactions} transactions`
                  : 'N/A'
              }
            />

            <KPICard
              title="Active BNPL Loans"
              value={
                activeBnplLoans !== null &&
                activeBnplLoans !== undefined
                  ? activeBnplLoans
                  : 'N/A'
              }
            />
          </>
        )}
      </div>

      {/* =========================================================
          GMV TREND
          ========================================================= */}
      <div className="bg-white p-4 rounded shadow">
        <div className="flex space-x-4 mb-4">
          {PERIODS.map(({ label, days }) => (
            <button
              key={label}
              onClick={() => setPeriod(days)}
              className={`px-4 py-2 rounded ${
                period === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={gmvTrend}>
              <CartesianGrid strokeDasharray="3 3" />

              <XAxis dataKey="date" />

              <YAxis
                tickFormatter={(value) =>
                  `${(Number(value) / 100000).toFixed(1)}L`
                }
              />

              <Tooltip
                formatter={(value) =>
                  formatIndianCurrency(Number(value))
                }
              />

              <Line
                type="monotone"
                dataKey="total_gmv"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* =========================================================
          BOTTOM ROW
          ========================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* =======================================================
            PAYMENT METHOD SUCCESS RATE
            ======================================================= */}
        <div className="bg-white p-4 rounded shadow">
          <h3 className="text-lg font-semibold mb-4">
            Payment Method Success Rate
          </h3>

          {loading ? (
            <LoadingSpinner />
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={paymentMethodBreakdown}>
                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="method" />

                <YAxis
                  domain={[0, 100]}
                  tickFormatter={(value) =>
                    `${Number(value).toFixed(0)}%`
                  }
                />

                <Tooltip
                  formatter={(value) =>
                    formatPercentage(value)
                  }
                />

                <Bar
                  dataKey="success_rate"
                  name="Success Rate"
                >
                  {paymentMethodBreakdown.map(
                    (entry, index) => (
                      <Cell
                        key={`payment-method-${entry.method}-${index}`}
                        fill={getPaymentMethodColor(entry.method)}
                      />
                    )
                  )}
                </Bar>

                <Legend
                  formatter={(value) => value}
                />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* =======================================================
            TOP MERCHANTS
            ======================================================= */}
        <div className="bg-white p-4 rounded shadow overflow-auto">
          <h3 className="text-lg font-semibold mb-4">
            Top Merchants
          </h3>

          {loading ? (
            <LoadingSpinner />
          ) : (
            <table className="w-full text-left">
              <thead>
                <tr>
                  <th className="border-b p-2">Rank</th>
                  <th className="border-b p-2">Merchant</th>
                  <th className="border-b p-2">GMV</th>
                  <th className="border-b p-2">
                    Success Rate
                  </th>
                </tr>
              </thead>

              <tbody>
                {topMerchants.map((merchant, index) => {
                  const successRate = merchant?.success_rate;
                  const successRateNumber = Number(successRate);

                  return (
                    <tr
                      key={`${
                        merchant?.merchant_name || 'merchant'
                      }-${index}`}
                      className="hover:bg-gray-100"
                    >
                      <td className="border-b p-2">
                        {index + 1}
                      </td>

                      <td className="border-b p-2">
                        {merchant?.merchant_name || 'N/A'}
                      </td>

                      <td className="border-b p-2">
                        {merchant?.gmv !== undefined &&
                        merchant?.gmv !== null
                          ? formatIndianCurrency(merchant.gmv)
                          : 'N/A'}
                      </td>

                      <td className="border-b p-2">
                        {successRate !== undefined &&
                        successRate !== null &&
                        !Number.isNaN(successRateNumber) ? (
                          <span
                            className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                              successRateNumber > 90
                                ? 'bg-green-100 text-green-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {successRateNumber.toFixed(2)}%
                          </span>
                        ) : (
                          <span className="text-gray-500">
                            N/A
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
}
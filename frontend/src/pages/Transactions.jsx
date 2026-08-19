import React, { useState, useEffect, useCallback } from 'react';
import { getTransactions, getTransaction } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner} from '../components/LoadingSpinner';
import { ToastProvider } from '../components/ToastProvider';
import { Modal } from '../components/Modal';
import { formatDateTimeIST, formatIndianCurrency } from '../utils/formatters';
import { EmptyState } from '../components/EmptyState';

const STATUS_OPTIONS = [
  { label: 'All Statuses', value: '' },
  { label: 'PENDING', value: 'PENDING' },
  { label: 'SUCCESS', value: 'SUCCESS' },
  { label: 'FAILED', value: 'FAILED' },
  { label: 'BLOCKED', value: 'BLOCKED' },
  { label: 'REFUNDED', value: 'REFUNDED' },
];

const PAYMENT_METHOD_OPTIONS = [
  { label: 'All Methods', value: '' },
  { label: 'UPI', value: 'UPI' },
  { label: 'CARD', value: 'CARD' },
  { label: 'WALLET', value: 'WALLET' },
  { label: 'NETBANKING', value: 'NETBANKING' },
];

function shortenTxId(txId) {
  if (!txId || txId.length < 8) return txId;
  return txId.slice(0, 4) + '...' + txId.slice(-4);
}

export default function Transactions() {
  // Draft filter state (form inputs)
  const [filters, setFilters] = useState({
    status: '',
    payment_method: '',
    start_date: '',
    end_date: '',
  });

  // Applied filters state (used for API requests)
  const [appliedFilters, setAppliedFilters] = useState({
    status: '',
    payment_method: '',
    start_date: '',
    end_date: '',
  });

  // Pagination state
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Data state
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);

  // Loading and error states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Slide-over detail state
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  // Fetch transactions list
  const fetchTransactions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        status: appliedFilters.status || undefined,
        payment_method: appliedFilters.payment_method || undefined,
        start_date: appliedFilters.start_date || undefined,
        end_date: appliedFilters.end_date || undefined,
        page,
        page_size: pageSize,
      };
      const data = await getTransactions(params);
      setTransactions(data.items);
      setTotal(data.total);
    } catch (err) {
      setError('Failed to load transactions. Please try again.');
      setTransactions([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [appliedFilters, page]);

  // Fetch transaction detail
  const fetchTransactionDetail = useCallback(async (transactionId) => {
    setDetailLoading(true);
    setDetailError(null);
    setSelectedTransaction(null);
    try {
      const data = await getTransaction(transactionId);
      setSelectedTransaction(data);
    } catch (err) {
      setDetailError('Failed to load transaction details.');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  // Handle Apply button click
  const handleApplyFilters = () => {
    setAppliedFilters(filters);
    setPage(1);
  };

  // Handle page change
  const handlePreviousPage = () => {
    if (page > 1) {
      setPage((p) => p - 1);
    }
  };

  const handleNextPage = () => {
    const lastPage = Math.ceil(total / pageSize);
    if (page < lastPage) {
      setPage((p) => p + 1);
    }
  };

  // Fetch transactions when appliedFilters or page changes
  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // Handle transaction ID copy
  const handleCopyTxId = (fullTxId) => {
    navigator.clipboard.writeText(fullTxId).then(() => {
      ToastProvider.toast.success('Transaction ID copied');
    });
  };

  // Handle row click to open detail slide-over
  const handleRowClick = (transactionId) => {
    setDetailOpen(true);
    setDetailLoading(true);
    setDetailError(null);
    setSelectedTransaction(null);
    fetchTransactionDetail(transactionId);
  };

  // Close detail slide-over
  const closeDetail = () => {
    setDetailOpen(false);
    setSelectedTransaction(null);
    setDetailError(null);
  };

  // Calculate last page
  const lastPage = Math.ceil(total / pageSize);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">Transactions</h1>

      {/* Filter Bar */}
      <div className="flex flex-wrap gap-4 mb-4 items-end">
        <div>
          <label htmlFor="status" className="block text-sm font-medium text-gray-700">
            Status
          </label>
          <select
            id="status"
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
      </div>

        <div>
          <label htmlFor="paymentMethod" className="block text-sm font-medium text-gray-700">
            Payment Method
          </label>
          <select
            id="paymentMethod"
            value={filters.payment_method}
            onChange={(e) => setFilters((f) => ({ ...f, payment_method: e.target.value }))}
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            {PAYMENT_METHOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="startDate" className="block text-sm font-medium text-gray-700">
            Start Date
          </label>
          <input
            type="date"
            id="startDate"
            value={filters.start_date}
            onChange={(e) => setFilters((f) => ({ ...f, start_date: e.target.value }))}
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            max={filters.end_date || undefined}
          />
        </div>

        <div>
          <label htmlFor="endDate" className="block text-sm font-medium text-gray-700">
            End Date
          </label>
          <input
            type="date"
            id="endDate"
            value={filters.end_date}
            onChange={(e) => setFilters((f) => ({ ...f, end_date: e.target.value }))}
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            min={filters.start_date || undefined}
          />
        </div>

        <div>
          <button
            onClick={handleApplyFilters}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            Apply
          </button>
        </div>
      </div>

      {/* Error message */}
      {error && (
        <div className="mb-4 text-red-600 font-medium" role="alert">
          {error}
        </div>
      )}

      {/* Transactions Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-md">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-indigo-100 border-b-4 border-indigo-700 shadow-md">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                TX ID
              </th>
              <th className="px-4 py-3 text-left text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                Merchant
              </th>
              <th className="px-4 py-3 text-right text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                Amount
              </th>
              <th className="px-4 py-3 text-left text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                Method
              </th>
              <th className="px-4 py-3 text-left text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                Status
              </th>
              <th className="px-4 py-3 text-center text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                Risk Score
              </th>
              <th className="px-4 py-3 text-left text-sm font-extrabold text-indigo-900 uppercase tracking-wider">
                IST Timestamp
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              // Loading skeleton rows
              Array.from({ length: pageSize }).map((_, idx) => (
                <tr key={idx} className="animate-pulse">
                  <td className="px-4 py-2">
                    <div className="h-4 bg-gray-300 rounded w-20"></div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="h-4 bg-gray-300 rounded w-24"></div>
                  </td>
                  <td className="px-4 py-2 text-right">
                    <div className="h-4 bg-gray-300 rounded w-16 mx-auto"></div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="h-4 bg-gray-300 rounded w-16"></div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="h-4 bg-gray-300 rounded w-20"></div>
                  </td>
                  <td className="px-4 py-2 text-center">
                    <div className="h-4 bg-gray-300 rounded w-12 mx-auto"></div>
                  </td>
                  <td className="px-4 py-2">
                    <div className="h-4 bg-gray-300 rounded w-32"></div>
                  </td>
                </tr>
              ))
            ) : total === 0 ? (
              <tr>
                <td colSpan="7" className="text-center py-8 text-gray-500">
                  <EmptyState message="No transactions found. Try adjusting your filters." />
                </td>
              </tr>
            ) : (
              transactions.map((tx) => (
                <tr
                  key={tx.transaction_id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleRowClick(tx.transaction_id)}
                >
                  <td className="px-4 py-2 flex items-center space-x-2">
                    <span
                      className="text-indigo-600 underline cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation();
                        // Open slide-over with details on clicking TX ID text
                        setDetailOpen(true);
                        fetchTransactionDetail(tx.transaction_id);
                      }}
                      title="Click to view transaction details"
                    >
                      {shortenTxId(tx.transaction_id)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCopyTxId(tx.transaction_id);
                      }}
                      aria-label="Copy full Transaction ID"
                      className="text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded"
                      title="Copy full Transaction ID"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M8 16h8M8 12h8m-6 8h6a2 2 0 002-2v-6a2 2 0 00-2-2h-6a2 2 0 00-2 2v6a2 2 0 002 2z"
                        />
                      </svg>
                    </button>
                  </td>
                  <td className="px-4 py-2">{tx.merchant_id}</td>
                  <td className="px-4 py-2 text-right font-mono">
                    {tx.currency === 'INR'
                      ? formatIndianCurrency(tx.amount)
                      : `${tx.currency} ${tx.amount.toLocaleString()}`}
                  </td>
                  <td className="px-4 py-2">
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-gray-200 text-gray-800">
                      {tx.payment_method}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <StatusBadge status={tx.status} />
                  </td>
                  <td className="px-4 py-2 text-center text-gray-500 font-mono">N/A</td>
                  <td className="px-4 py-2">{formatDateTimeIST(tx.created_at)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-between items-center mt-4">
        <button
          onClick={handlePreviousPage}
          disabled={page === 1}
          className={`px-3 py-1 rounded border ${
            page === 1
              ? 'border-gray-300 text-gray-400 cursor-not-allowed'
              : 'border-indigo-600 text-indigo-600 hover:bg-indigo-50'
          }`}
        >
          Previous
        </button>
        <span className="text-sm text-gray-700">
          Page {page} of {lastPage || 1}
        </span>
        <button
          onClick={handleNextPage}
          disabled={page === lastPage || lastPage === 0}
          className={`px-3 py-1 rounded border ${
            page === lastPage || lastPage === 0
              ? 'border-gray-300 text-gray-400 cursor-not-allowed'
              : 'border-indigo-600 text-indigo-600 hover:bg-indigo-50'
          }`}
        >
          Next
        </button>
      </div>

      {/* Slide-over detail panel */}
      {detailOpen && (
        <Modal isOpen={detailOpen} onClose={closeDetail} slideOver>
          <div className="p-6 w-96 max-w-full h-full overflow-y-auto bg-white">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">TRANSACTION DETAILS</h2>
              <button
                onClick={closeDetail}
                aria-label="Close"
                className="text-gray-500 hover:text-gray-700"
              >
                &times;
              </button>
            </div>

            {detailLoading ? (
              <LoadingSpinner />
            ) : detailError ? (
              <div className="text-red-600 font-medium">{detailError}</div>
            ) : selectedTransaction ? (
              <div className="space-y-4 text-sm text-gray-700">
                <div>
                  <div className="font-semibold">Transaction ID</div>
                  <div className="font-mono break-all">{selectedTransaction.transaction_id || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Merchant</div>
                  <div>{selectedTransaction.merchant_id || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Amount</div>
                  <div>
                    {selectedTransaction.currency === 'INR'
                      ? formatIndianCurrency(selectedTransaction.amount)
                      : selectedTransaction.currency
                      ? `${selectedTransaction.currency} ${selectedTransaction.amount.toLocaleString()}`
                      : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="font-semibold">Payment Method</div>
                  <div>{selectedTransaction.payment_method || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Status</div>
                  <StatusBadge status={selectedTransaction.status || 'N/A'} />
                </div>
                <div>
                  <div className="font-semibold">Gateway</div>
                  <div>{selectedTransaction.gateway_used || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Razorpay Order ID</div>
                  <div>{selectedTransaction.razorpay_order_id || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Razorpay Payment ID</div>
                  <div>{selectedTransaction.razorpay_payment_id || 'N/A'}</div>
                </div>
                <div>
                  <div className="font-semibold">Created</div>
                  <div>{selectedTransaction.created_at ? formatDateTimeIST(selectedTransaction.created_at) + ' IST' : 'N/A'}</div>
                </div>

                {/* Risk & Fraud section */}
                <div className="mt-6 border-t pt-4 text-gray-500 text-xs">
                  <div className="font-semibold mb-2">Risk & Fraud</div>
                  <div>
                    <strong>Risk Score:</strong> Not available
                  </div>
                  <div>
                    <strong>Triggered Rules:</strong> Not available
                  </div>
                  <div>
                    <strong>Timeline:</strong> Not available
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </Modal>
      )}
    </div>
  );
}
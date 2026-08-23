import React, { useState, useEffect, useCallback } from 'react';

import {
  getTransactions,
  getTransaction,
  raiseDispute,
} from '../api/client';

import { StatusBadge } from '../components/StatusBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ToastProvider, useToast } from '../components/ToastProvider';
import { Modal } from '../components/Modal';
import {
  formatDateTimeIST,
  formatIndianCurrency,
} from '../utils/formatters';
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

/*
 * Inner component.
 *
 * IMPORTANT:
 * This component is rendered INSIDE ToastProvider,
 * so useToast() is safe here.
 */
function TransactionsContent() {
  // Draft filter state
  const [filters, setFilters] = useState({
    status: '',
    payment_method: '',
    start_date: '',
    end_date: '',
  });

  // Applied filters state
  const [appliedFilters, setAppliedFilters] = useState({
    status: '',
    payment_method: '',
    start_date: '',
    end_date: '',
  });

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // Data
  const [transactions, setTransactions] = useState([]);
  const [total, setTotal] = useState(0);

  // Loading/error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Transaction detail slide-over
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);
  const [selectedTransaction, setSelectedTransaction] = useState(null);

  // Transaction ID search
  const [transactionIdSearch, setTransactionIdSearch] = useState('');

  // Dispute modal
  const [disputeModalOpen, setDisputeModalOpen] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');
  const [disputeDescription, setDisputeDescription] = useState('');
  const [disputeSubmitting, setDisputeSubmitting] = useState(false);
  const [disputeSubmitted, setDisputeSubmitted] = useState(false);

  // Toast hook is now safely inside ToastProvider
  const { addToast } = useToast();

  // Calculate last page
  const lastPage = Math.max(1, Math.ceil(total / pageSize));

  // ------------------------------------------------------------
  // Fetch transactions
  // ------------------------------------------------------------

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

      setTransactions(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load transactions:', err);

      setError('Failed to load transactions. Please try again.');
      setTransactions([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [appliedFilters, page]);

  // ------------------------------------------------------------
  // Search transaction by ID
  // ------------------------------------------------------------

  const handleTransactionIdSearch = async () => {
    const transactionId = transactionIdSearch.trim();

    if (!transactionId) {
      addToast({
        type: 'error',
        message: 'Please enter a Transaction ID.',
      });
      return;
    }

    setDetailOpen(true);
    setDetailLoading(true);
    setDetailError(null);
    setSelectedTransaction(null);

    try {
      const data = await getTransaction(transactionId);

      setSelectedTransaction(data);

      // Reset dispute state for the newly opened transaction.
      setDisputeSubmitted(false);
      setDisputeModalOpen(false);
      setDisputeReason('');
      setDisputeDescription('');
    } catch (err) {
      console.error('Failed to find transaction:', err);

      setDetailOpen(false);
      setDetailError(null);

      addToast({
        type: 'error',
        message: 'Transaction not found. Please check the Transaction ID.',
      });
    } finally {
      setDetailLoading(false);
    }
  };

  const handleTransactionIdSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleTransactionIdSearch();
    }
  };

  // ------------------------------------------------------------
  // Fetch transaction detail
  // ------------------------------------------------------------

  const fetchTransactionDetail = useCallback(async (transactionId) => {
    setDetailLoading(true);
    setDetailError(null);
    setSelectedTransaction(null);

    // Reset dispute state whenever a new transaction is opened
    setDisputeSubmitted(false);
    setDisputeModalOpen(false);
    setDisputeReason('');
    setDisputeDescription('');

    try {
      const data = await getTransaction(transactionId);
      setSelectedTransaction(data);
    } catch (err) {
      console.error('Failed to load transaction detail:', err);
      setDetailError('Failed to load transaction details.');
    } finally {
      setDetailLoading(false);
    }
  }, []);

  // ------------------------------------------------------------
  // Fetch transactions whenever filters/page change
  // ------------------------------------------------------------

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  // ------------------------------------------------------------
  // Apply filters
  // ------------------------------------------------------------

  const handleApplyFilters = () => {
    setAppliedFilters(filters);
    setPage(1);
  };

  // ------------------------------------------------------------
  // Pagination
  // ------------------------------------------------------------

  const handlePreviousPage = () => {
    if (page > 1) {
      setPage((p) => p - 1);
    }
  };

  const handleNextPage = () => {
    if (page < lastPage) {
      setPage((p) => p + 1);
    }
  };

  // ------------------------------------------------------------
  // Copy transaction ID
  // ------------------------------------------------------------

  const handleCopyTxId = async (fullTxId) => {
    try {
      await navigator.clipboard.writeText(fullTxId);

      addToast({
        type: 'success',
        message: 'Transaction ID copied',
      });
    } catch (err) {
      console.error('Failed to copy transaction ID:', err);

      addToast({
        type: 'error',
        message: 'Failed to copy Transaction ID',
      });
    }
  };

  // ------------------------------------------------------------
  // Open transaction detail
  // ------------------------------------------------------------

  const handleRowClick = (transactionId) => {
    setDetailOpen(true);
    fetchTransactionDetail(transactionId);
  };

  // ------------------------------------------------------------
  // Close transaction detail
  // ------------------------------------------------------------

  const closeDetail = () => {
    setDetailOpen(false);
    setSelectedTransaction(null);
    setDetailError(null);

    setDisputeModalOpen(false);
    setDisputeReason('');
    setDisputeDescription('');
    setDisputeSubmitting(false);
    setDisputeSubmitted(false);
  };

  // ------------------------------------------------------------
  // Open dispute modal
  // ------------------------------------------------------------

  const openDisputeModal = () => {
    setDisputeModalOpen(true);
    setDisputeReason('');
    setDisputeDescription('');
    setDisputeSubmitting(false);
  };

  // ------------------------------------------------------------
  // Close dispute modal
  // ------------------------------------------------------------

  const closeDisputeModal = () => {
    if (disputeSubmitting) {
      return;
    }

    setDisputeModalOpen(false);
  };

  // ------------------------------------------------------------
  // Raise dispute
  //
  // IMPORTANT:
  // Named handleRaiseDispute to avoid conflicting with the
  // imported raiseDispute API function.
  // ------------------------------------------------------------

  const handleRaiseDispute = async () => {
    if (!disputeReason || !disputeDescription.trim()) {
      addToast({
        type: 'error',
        message: 'Reason and description are required.',
      });
      return;
    }

    if (!selectedTransaction) {
      addToast({
        type: 'error',
        message: 'No transaction selected.',
      });
      return;
    }

    if (selectedTransaction.status !== 'SUCCESS') {
      addToast({
        type: 'error',
        message: 'Only successful transactions can be disputed.',
      });
      return;
    }

    setDisputeSubmitting(true);

    try {
      await raiseDispute(
        selectedTransaction.transaction_id,
        disputeReason,
        disputeDescription.trim()
      );

      setDisputeSubmitted(true);
      setDisputeModalOpen(false);

      addToast({
        type: 'success',
        message: 'Dispute raised successfully.',
      });
    } catch (err) {
      console.error('Failed to raise dispute:', err);

      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Failed to raise dispute.';

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setDisputeSubmitting(false);
    }
  };

  // ------------------------------------------------------------
  // Render
  // ------------------------------------------------------------

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-4">
        Transactions
      </h1>

      {/* ------------------------------------------------------ */}
      {/* Filter Bar */}
      {/* ------------------------------------------------------ */}

      <div className="flex flex-wrap gap-4 mb-4 items-end">

        {/* Status */}
        <div>
          <label
            htmlFor="status"
            className="block text-sm font-medium text-gray-700"
          >
            Status
          </label>

          <select
            id="status"
            value={filters.status}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                status: e.target.value,
              }))
            }
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Payment Method */}
        <div>
          <label
            htmlFor="paymentMethod"
            className="block text-sm font-medium text-gray-700"
          >
            Payment Method
          </label>

          <select
            id="paymentMethod"
            value={filters.payment_method}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                payment_method: e.target.value,
              }))
            }
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            {PAYMENT_METHOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Start Date */}
        <div>
          <label
            htmlFor="startDate"
            className="block text-sm font-medium text-gray-700"
          >
            Start Date
          </label>

          <input
            type="date"
            id="startDate"
            value={filters.start_date}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                start_date: e.target.value,
              }))
            }
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            max={filters.end_date || undefined}
          />
        </div>

        {/* End Date */}
        <div>
          <label
            htmlFor="endDate"
            className="block text-sm font-medium text-gray-700"
          >
            End Date
          </label>

          <input
            type="date"
            id="endDate"
            value={filters.end_date}
            onChange={(e) =>
              setFilters((f) => ({
                ...f,
                end_date: e.target.value,
              }))
            }
            className="mt-1 block w-40 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            min={filters.start_date || undefined}
          />
        </div>

        {/* Apply */}
        <div>
          <button
            type="button"
            onClick={handleApplyFilters}
            className="inline-block px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
          >
            Apply
          </button>
        </div>

        {/* Transaction ID Search */}
        <div className="flex items-end gap-2">
          <div>
            <label
              htmlFor="transactionIdSearch"
              className="block text-sm font-medium text-gray-700"
            >
              Transaction ID
            </label>
            <input
              id="transactionIdSearch"
              type="text"
              value={transactionIdSearch}
              onChange={(e) => setTransactionIdSearch(e.target.value)}
              onKeyDown={handleTransactionIdSearchKeyDown}
              placeholder="Enter Transaction ID"
              className="mt-1 block w-64 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <button
            type="button"
            onClick={handleTransactionIdSearch}
            className="inline-block px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
          >
            Search
          </button>
        </div>
      </div>

      {/* ------------------------------------------------------ */}
      {/* Error */}
      {/* ------------------------------------------------------ */}

      {error && (
        <div
          className="mb-4 text-red-600 font-medium"
          role="alert"
        >
          {error}
        </div>
      )}

      {/* ------------------------------------------------------ */}
      {/* Transactions Table */}
      {/* ------------------------------------------------------ */}

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

            {/* Loading */}
            {loading ? (
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
                <td
                  colSpan="7"
                  className="text-center py-8 text-gray-500"
                >
                  <EmptyState message="No transactions found. Try adjusting your filters." />
                </td>
              </tr>

            ) : (

              transactions.map((tx) => (
                <tr
                  key={tx.transaction_id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() =>
                    handleRowClick(tx.transaction_id)
                  }
                >

                  {/* TX ID */}
                  <td className="px-4 py-2 flex items-center space-x-2">

                    <span
                      className="text-indigo-600 underline cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation();

                        setDetailOpen(true);
                        fetchTransactionDetail(
                          tx.transaction_id
                        );
                      }}
                      title="Click to view transaction details"
                    >
                      {shortenTxId(tx.transaction_id)}
                    </span>

                    <button
                      type="button"
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

                  {/* Merchant */}
                  <td className="px-4 py-2">
                    {tx.merchant_id}
                  </td>

                  {/* Amount */}
                  <td className="px-4 py-2 text-right font-mono">
                    {tx.currency === 'INR'
                      ? formatIndianCurrency(tx.amount)
                      : `${tx.currency} ${tx.amount?.toLocaleString?.() ?? tx.amount}`}
                  </td>

                  {/* Method */}
                  <td className="px-4 py-2">
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-gray-200 text-gray-800">
                      {tx.payment_method}
                    </span>
                  </td>

                  {/* Status */}
                  <td className="px-4 py-2">
                    <StatusBadge status={tx.status} />
                  </td>

                  {/* Risk */}
                  <td className="px-4 py-2 text-center text-gray-500 font-mono">
                    N/A
                  </td>

                  {/* Timestamp */}
                  <td className="px-4 py-2">
                    {formatDateTimeIST(tx.created_at)}
                  </td>

                </tr>
              ))

            )}

          </tbody>
        </table>
      </div>

      {/* ------------------------------------------------------ */}
      {/* Pagination */}
      {/* ------------------------------------------------------ */}

      <div className="flex justify-between items-center mt-4">

        <button
          type="button"
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
          Page {page} of {lastPage}
        </span>

        <button
          type="button"
          onClick={handleNextPage}
          disabled={page === lastPage}
          className={`px-3 py-1 rounded border ${
            page === lastPage
              ? 'border-gray-300 text-gray-400 cursor-not-allowed'
              : 'border-indigo-600 text-indigo-600 hover:bg-indigo-50'
          }`}
        >
          Next
        </button>

      </div>

      {/* ------------------------------------------------------ */}
      {/* Transaction Detail Slide-over */}
      {/* ------------------------------------------------------ */}

      {detailOpen && (
        <Modal
          isOpen={detailOpen}
          onClose={closeDetail}
          slideOver
        >
          <div className="p-6 w-96 max-w-full h-full overflow-y-auto bg-white">

            <div className="flex justify-between items-center mb-4">

              <h2 className="text-lg font-semibold">
                TRANSACTION DETAILS
              </h2>

              <button
                type="button"
                onClick={closeDetail}
                aria-label="Close"
                className="text-gray-500 hover:text-gray-700"
              >
                &times;
              </button>

            </div>

            {/* Detail loading */}
            {detailLoading ? (

              <LoadingSpinner />

            ) : detailError ? (

              <div className="text-red-600 font-medium">
                {detailError}
              </div>

            ) : selectedTransaction ? (

              <div className="space-y-4 text-sm text-gray-700">

                {/* Transaction ID */}
                <div>
                  <div className="font-semibold">
                    Transaction ID
                  </div>

                  <div className="font-mono break-all">
                    {selectedTransaction.transaction_id || 'N/A'}
                  </div>
                </div>

                {/* Merchant */}
                <div>
                  <div className="font-semibold">
                    Merchant
                  </div>

                  <div>
                    {selectedTransaction.merchant_id || 'N/A'}
                  </div>
                </div>

                {/* Amount */}
                <div>
                  <div className="font-semibold">
                    Amount
                  </div>

                  <div>
                    {selectedTransaction.currency === 'INR'
                      ? formatIndianCurrency(
                          selectedTransaction.amount
                        )
                      : selectedTransaction.currency
                      ? `${selectedTransaction.currency} ${
                          selectedTransaction.amount?.toLocaleString?.() ??
                          selectedTransaction.amount
                        }`
                      : 'N/A'}
                  </div>
                </div>

                {/* Payment Method */}
                <div>
                  <div className="font-semibold">
                    Payment Method
                  </div>

                  <div>
                    {selectedTransaction.payment_method || 'N/A'}
                  </div>
                </div>

                {/* Status */}
                <div>
                  <div className="font-semibold">
                    Status
                  </div>

                  <StatusBadge
                    status={
                      selectedTransaction.status || 'N/A'
                    }
                  />
                </div>

                {/* Gateway */}
                <div>
                  <div className="font-semibold">
                    Gateway
                  </div>

                  <div>
                    {selectedTransaction.gateway_used || 'N/A'}
                  </div>
                </div>

                {/* Razorpay Order ID */}
                <div>
                  <div className="font-semibold">
                    Razorpay Order ID
                  </div>

                  <div className="font-mono break-all">
                    {selectedTransaction.razorpay_order_id ||
                      'N/A'}
                  </div>
                </div>

                {/* Razorpay Payment ID */}
                <div>
                  <div className="font-semibold">
                    Razorpay Payment ID
                  </div>

                  <div className="font-mono break-all">
                    {selectedTransaction.razorpay_payment_id ||
                      'N/A'}
                  </div>
                </div>

                {/* Created */}
                <div>
                  <div className="font-semibold">
                    Created
                  </div>

                  <div>
                    {selectedTransaction.created_at
                      ? `${formatDateTimeIST(
                          selectedTransaction.created_at
                        )} IST`
                      : 'N/A'}
                  </div>
                </div>

                {/* ------------------------------------------------ */}
                {/* Risk & Fraud */}
                {/* ------------------------------------------------ */}

                <div className="mt-6 border-t pt-4 text-gray-500 text-xs">

                  <div className="font-semibold mb-2">
                    Risk & Fraud
                  </div>

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

                {/* ------------------------------------------------ */}
                {/* Raise Dispute */}
                {/* ------------------------------------------------ */}

                {selectedTransaction.status === 'SUCCESS' &&
                  !disputeSubmitted && (
                    <button
                      type="button"
                      onClick={openDisputeModal}
                      className="w-full mt-4 rounded-md bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 disabled:opacity-50"
                    >
                      Raise Dispute
                    </button>
                  )}

                {/* Dispute submitted */}
                {disputeSubmitted && (
                  <button
                    type="button"
                    disabled
                    className="btn btn-success w-full mt-4 cursor-not-allowed"
                  >
                    Dispute Raised
                  </button>
                )}

              </div>

            ) : null}

            {/* -------------------------------------------------- */}
            {/* Raise Dispute Modal */}
            {/* -------------------------------------------------- */}

            {disputeModalOpen && (
              <Modal
                isOpen={disputeModalOpen}
                onClose={closeDisputeModal}
              >
                <div className="p-6">

                  <h3 className="text-lg font-semibold mb-4">
                    Raise Dispute
                  </h3>

                  {/* Reason */}
                  <label
                    className="block mb-2 font-medium"
                    htmlFor="disputeReason"
                  >
                    Reason
                  </label>

                  <select
                    id="disputeReason"
                    value={disputeReason}
                    onChange={(e) =>
                      setDisputeReason(e.target.value)
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
                    required
                    disabled={disputeSubmitting}
                  >
                    <option value="">
                      Select reason
                    </option>

                    <option value="FRAUD">
                      FRAUD
                    </option>

                    <option value="DUPLICATE">
                      DUPLICATE
                    </option>

                    <option value="NOT_RECEIVED">
                      NOT_RECEIVED
                    </option>

                    <option value="WRONG_AMOUNT">
                      WRONG_AMOUNT
                    </option>
                  </select>

                  {/* Description */}
                  <label
                    className="block mb-2 font-medium"
                    htmlFor="disputeDescription"
                  >
                    Description
                  </label>

                  <textarea
                    id="disputeDescription"
                    value={disputeDescription}
                    onChange={(e) =>
                      setDisputeDescription(e.target.value)
                    }
                    className="w-full border border-gray-300 rounded px-3 py-2 mb-4"
                    rows={4}
                    required
                    disabled={disputeSubmitting}
                    placeholder="Describe the reason for this dispute..."
                  />

                  {/* Buttons */}
                  <div className="flex justify-end gap-2">

                    <button
                      type="button"
                      onClick={closeDisputeModal}
                      disabled={disputeSubmitting}
                      className="inline-block px-4 py-2 text-sm font-semibold text-gray-700 bg-gray-200 rounded hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-1"
                    >
                      Cancel
                    </button>

                    <button
                      type="button"
                      onClick={handleRaiseDispute}
                      className="inline-block px-4 py-2 text-sm font-semibold text-white bg-red-600 rounded hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1"
                      disabled={
                        disputeSubmitting ||
                        !disputeReason ||
                        !disputeDescription.trim()
                      }
                    >
                      {disputeSubmitting
                        ? 'Raising...'
                        : 'Raise Dispute'}
                    </button>

                  </div>

                </div>
              </Modal>
            )}

          </div>
        </Modal>
      )}

    </div>
  );
}

/*
 * Outer wrapper.
 *
 * This is the important fix:
 *
 * Transactions
 *   └── ToastProvider
 *         └── TransactionsContent
 *               └── useToast()
 *
 * Therefore useToast() is now inside ToastProvider.
 */
export default function Transactions() {
  return (
    <ToastProvider>
      <TransactionsContent />
    </ToastProvider>
  );
}
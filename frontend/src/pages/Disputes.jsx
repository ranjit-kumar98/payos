import React, { useCallback, useEffect, useMemo, useState } from 'react';

import {
  getDisputes,
  moveDisputeToReview,
  resolveDispute,
  rejectDispute,
} from '../api/client';

import { KPICard } from '../components/KPICard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { Modal } from '../components/Modal';
import { ToastProvider, useToast } from '../components/ToastProvider';

const DISPUTE_STATUSES = [
  'RAISED',
  'UNDER_REVIEW',
  'RESOLVED',
  'REJECTED',
];

const STATUS_LABELS = {
  RAISED: 'Raised',
  UNDER_REVIEW: 'Under Review',
  RESOLVED: 'Resolved',
  REJECTED: 'Rejected',
};

const STATUS_STYLES = {
  RAISED: 'bg-blue-100 text-blue-800 border-blue-200',
  UNDER_REVIEW: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  RESOLVED: 'bg-green-100 text-green-800 border-green-200',
  REJECTED: 'bg-gray-100 text-gray-700 border-gray-200',
};

const REASON_STYLES = {
  FRAUD: 'bg-red-100 text-red-800 border-red-200',
  DUPLICATE: 'bg-orange-100 text-orange-800 border-orange-200',
  NOT_RECEIVED: 'bg-blue-100 text-blue-800 border-blue-200',
  WRONG_AMOUNT: 'bg-purple-100 text-purple-800 border-purple-200',
};

function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || String(item))
      .join(', ');
  }

  if (typeof error?.response?.data?.message === 'string') {
    return error.response.data.message;
  }

  if (error?.message) {
    return error.message;
  }

  return fallback;
}

function formatStatus(status) {
  return STATUS_LABELS[status] || status || 'Unknown';
}

function formatReason(reason) {
  if (!reason) return 'Unknown';

  return String(reason)
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDateTimeIST(value) {
  if (!value) return 'N/A';

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return 'N/A';
  }

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'Asia/Kolkata',
  }).format(date);
}

function formatDuration(milliseconds) {
  if (
    milliseconds === null ||
    milliseconds === undefined ||
    Number.isNaN(milliseconds)
  ) {
    return 'N/A';
  }

  const totalMinutes = Math.max(
    0,
    Math.floor(milliseconds / 60000)
  );

  if (totalMinutes < 60) {
    return `${totalMinutes} min`;
  }

  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;

  if (hours < 24) {
    return minutes > 0
      ? `${hours}h ${minutes}m`
      : `${hours}h`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;

  return remainingHours > 0
    ? `${days}d ${remainingHours}h`
    : `${days}d`;
}

function getResolutionDuration(dispute) {
  if (!dispute?.raised_at || !dispute?.resolved_at) {
    return null;
  }

  const raised = new Date(dispute.raised_at).getTime();
  const resolved = new Date(dispute.resolved_at).getTime();

  if (
    Number.isNaN(raised) ||
    Number.isNaN(resolved)
  ) {
    return null;
  }

  return Math.max(0, resolved - raised);
}

function getDaysOpen(dispute) {
  if (!dispute?.raised_at) {
    return 'N/A';
  }

  const raised = new Date(dispute.raised_at).getTime();

  if (Number.isNaN(raised)) {
    return 'N/A';
  }

  const end =
    dispute.resolved_at
      ? new Date(dispute.resolved_at).getTime()
      : Date.now();

  if (Number.isNaN(end)) {
    return 'N/A';
  }

  const days = Math.floor(
    Math.max(0, end - raised) /
      (1000 * 60 * 60 * 24)
  );

  return `${days}d`;
}

function getSlaInfo(dispute) {
  if (dispute?.is_sla_breached) {
    return {
      label: 'SLA Breached',
      className:
        'bg-red-100 text-red-700 border-red-200',
    };
  }

  if (!dispute?.sla_deadline) {
    return {
      label: 'SLA N/A',
      className:
        'bg-gray-100 text-gray-600 border-gray-200',
    };
  }

  const deadline = new Date(
    dispute.sla_deadline
  ).getTime();

  if (Number.isNaN(deadline)) {
    return {
      label: 'SLA N/A',
      className:
        'bg-gray-100 text-gray-600 border-gray-200',
    };
  }

  const remaining = deadline - Date.now();

  if (remaining <= 0) {
    return {
      label: 'SLA Breached',
      className:
        'bg-red-100 text-red-700 border-red-200',
    };
  }

  const hours = remaining / (1000 * 60 * 60);

  if (hours < 24) {
    return {
      label: `${Math.max(1, Math.ceil(hours))}h left`,
      className:
        'bg-orange-100 text-orange-700 border-orange-200',
    };
  }

  const days = Math.ceil(hours / 24);

  return {
    label: `${days}d left`,
    className:
      'bg-green-100 text-green-700 border-green-200',
  };
}

function getDisputesFromResponse(response) {
  /*
   * client.js currently returns the Axios response
   * for getDisputes().
   *
   * Expected backend response:
   * {
   *   disputes: [...],
   *   total: number
   * }
   */

  const data = response?.data;

  if (!data) {
    return [];
  }

  if (Array.isArray(data)) {
    return data;
  }

  if (Array.isArray(data.disputes)) {
    return data.disputes;
  }

  return [];
}

function CopyButton({ value }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (event) => {
    event.stopPropagation();

    if (!value) return;

    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);

      window.setTimeout(() => {
        setCopied(false);
      }, 1200);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-1 text-gray-400 hover:text-indigo-600"
      title="Copy ID"
      aria-label="Copy ID"
    >
      {copied ? '✓' : '⧉'}
    </button>
  );
}

function StatusBadge({ status }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-semibold ${
        STATUS_STYLES[status] ||
        'bg-gray-100 text-gray-700 border-gray-200'
      }`}
    >
      {formatStatus(status)}
    </span>
  );
}

function ReasonBadge({ reason }) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-semibold ${
        REASON_STYLES[reason] ||
        'bg-gray-100 text-gray-700 border-gray-200'
      }`}
    >
      {formatReason(reason)}
    </span>
  );
}

function DisputeCard({ dispute, onClick }) {
  const sla = getSlaInfo(dispute);

  const handleCardKeyDown = (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick(dispute);
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onClick(dispute)}
      onKeyDown={handleCardKeyDown}
      className="w-full text-left bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md hover:border-indigo-300 transition focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer"
    >
      {/* ID + status */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="text-sm font-semibold text-gray-900">
            #{String(dispute.id || '').slice(0, 8)}
            <CopyButton value={dispute.id} />
          </div>

          <div className="mt-1 text-xs text-gray-500">
            TX: {String(dispute.transaction_id || '').slice(0, 8)}
            <CopyButton value={dispute.transaction_id} />
          </div>
        </div>

        <StatusBadge status={dispute.status} />
      </div>

      {/* Reason */}
      <div className="mt-4">
        <ReasonBadge reason={dispute.reason} />
      </div>

      {/* Merchant */}
      <div className="mt-4">
        <div className="text-xs text-gray-500">
          Merchant
        </div>

        <div
          className="mt-1 text-sm font-medium text-gray-800 truncate"
          title={dispute.merchant_id}
        >
          {dispute.merchant_id || 'N/A'}
        </div>
      </div>

      {/* Days + SLA */}
      <div className="mt-4 flex items-center justify-between gap-2">
        <div>
          <div className="text-xs text-gray-500">
            Days Open
          </div>

          <div className="text-sm font-semibold text-gray-800">
            {getDaysOpen(dispute)}
          </div>
        </div>

        <span
          className={`inline-flex items-center px-2 py-1 rounded-full border text-xs font-semibold ${sla.className}`}
        >
          {sla.label}
        </span>
      </div>

      {/* Raised date */}
      <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-400">
        Raised {formatDateTimeIST(dispute.raised_at)}
      </div>
    </div>
  );
}

function DetailRow({ label, value, copy = false }) {
  return (
    <div>
      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </div>

      <div className="mt-1 text-sm text-gray-900 break-all">
        {value || 'N/A'}

        {copy && value && (
          <CopyButton value={value} />
        )}
      </div>
    </div>
  );
}

function DisputeDetails({
  dispute,
  onMoveToReview,
  onResolve,
  onReject,
  actionLoading,
}) {
  const [resolutionNotes, setResolutionNotes] =
    useState('');

  const isRaised = dispute.status === 'RAISED';
  const isUnderReview =
    dispute.status === 'UNDER_REVIEW';

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <DetailRow
          label="Dispute ID"
          value={dispute.id}
          copy
        />

        <DetailRow
          label="Transaction ID"
          value={dispute.transaction_id}
          copy
        />

        <DetailRow
          label="Merchant ID"
          value={dispute.merchant_id}
          copy
        />

        <DetailRow
          label="Reason"
          value={formatReason(dispute.reason)}
        />

        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Status
          </div>

          <div className="mt-2">
            <StatusBadge status={dispute.status} />
          </div>
        </div>

        <div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            SLA
          </div>

          <div className="mt-2">
            {(() => {
              const sla = getSlaInfo(dispute);

              return (
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-full border text-xs font-semibold ${sla.className}`}
                >
                  {sla.label}
                </span>
              );
            })()}
          </div>
        </div>

        <DetailRow
          label="Raised At"
          value={formatDateTimeIST(
            dispute.raised_at
          )}
        />

        <DetailRow
          label="SLA Deadline"
          value={formatDateTimeIST(
            dispute.sla_deadline
          )}
        />

        <DetailRow
          label="Days Open"
          value={getDaysOpen(dispute)}
        />

        <DetailRow
          label="Updated At"
          value={formatDateTimeIST(
            dispute.updated_at
          )}
        />

        {dispute.resolved_at && (
          <DetailRow
            label="Resolved At"
            value={formatDateTimeIST(
              dispute.resolved_at
            )}
          />
        )}
      </div>

      {/* Description */}
      {dispute.description && (
        <div>
          <div className="text-sm font-semibold text-gray-800 mb-2">
            Description
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap">
            {dispute.description}
          </div>
        </div>
      )}

      {/* Existing resolution notes */}
      {dispute.resolution_notes && (
        <div>
          <div className="text-sm font-semibold text-gray-800 mb-2">
            Resolution Notes
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 text-sm text-gray-700 whitespace-pre-wrap">
            {dispute.resolution_notes}
          </div>
        </div>
      )}

      {/* Actions */}
      {isRaised && (
        <div className="border-t border-gray-200 pt-5">
          <button
            type="button"
            onClick={onMoveToReview}
            disabled={actionLoading}
            className="w-full px-4 py-2.5 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {actionLoading
              ? 'Moving to Review...'
              : 'Move to Review'}
          </button>
        </div>
      )}

      {isUnderReview && (
        <div className="border-t border-gray-200 pt-5">
          <label
            htmlFor="resolution-notes"
            className="block text-sm font-semibold text-gray-800 mb-2"
          >
            Resolution / Rejection Notes
          </label>

          <textarea
            id="resolution-notes"
            value={resolutionNotes}
            onChange={(event) =>
              setResolutionNotes(
                event.target.value
              )
            }
            rows={5}
            disabled={actionLoading}
            placeholder="Enter notes before resolving or rejecting this dispute..."
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 outline-none resize-y disabled:bg-gray-100"
          />

          <div className="mt-3 flex gap-3">
            <button
              type="button"
              onClick={() =>
                onResolve(resolutionNotes)
              }
              disabled={
                actionLoading ||
                !resolutionNotes.trim()
              }
              className="flex-1 px-4 py-2.5 rounded-lg bg-green-600 text-white text-sm font-semibold hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading
                ? 'Processing...'
                : 'Resolve'}
            </button>

            <button
              type="button"
              onClick={() =>
                onReject(resolutionNotes)
              }
              disabled={
                actionLoading ||
                !resolutionNotes.trim()
              }
              className="flex-1 px-4 py-2.5 rounded-lg bg-red-600 text-white text-sm font-semibold hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {actionLoading
                ? 'Processing...'
                : 'Reject'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function DisputesContent() {
  const { addToast } = useToast();

  const [allDisputes, setAllDisputes] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState('');

  const [selectedDispute, setSelectedDispute] =
    useState(null);

  const [actionLoading, setActionLoading] =
    useState(false);

  const [filterStatus, setFilterStatus] =
    useState('ALL');

  /*
   * Load the complete dispute list.
   *
   * We intentionally fetch all disputes once and perform
   * Kanban filtering locally so the stats remain based on
   * the complete dispute dataset rather than whichever
   * status happens to be selected in the filter.
   */
  const loadDisputes = useCallback(async () => {
    setLoading(true);
    setError('');

    try {
      const response = await getDisputes();
      const data = getDisputesFromResponse(response);

      setAllDisputes(data);
    } catch (err) {
      console.error(
        'Failed to load disputes:',
        err
      );

      setAllDisputes([]);

      setError(
        getErrorMessage(
          err,
          'Failed to load disputes.'
        )
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDisputes();
  }, [loadDisputes]);

  /*
   * Filter only affects the visible Kanban cards.
   */
  const visibleDisputes = useMemo(() => {
    if (filterStatus === 'ALL') {
      return allDisputes;
    }

    return allDisputes.filter(
      (dispute) =>
        dispute.status === filterStatus
    );
  }, [allDisputes, filterStatus]);

  /*
   * Kanban columns.
   */
  const disputesByStatus = useMemo(() => {
    const columns = {
      RAISED: [],
      UNDER_REVIEW: [],
      RESOLVED: [],
      REJECTED: [],
    };

    visibleDisputes.forEach((dispute) => {
      if (columns[dispute.status]) {
        columns[dispute.status].push(
          dispute
        );
      }
    });

    return columns;
  }, [visibleDisputes]);

  /*
   * Stats are calculated from ALL disputes,
   * not the selected visual filter.
   */
  const averageResolutionTime = useMemo(() => {
    const completedDisputes =
      allDisputes.filter(
        (dispute) =>
          dispute.resolved_at &&
          (dispute.status === 'RESOLVED' ||
            dispute.status === 'REJECTED')
      );

    if (completedDisputes.length === 0) {
      return 'N/A';
    }

    const durations =
      completedDisputes
        .map(getResolutionDuration)
        .filter(
          (duration) => duration !== null
        );

    if (durations.length === 0) {
      return 'N/A';
    }

    const total =
      durations.reduce(
        (sum, duration) =>
          sum + duration,
        0
      );

    return formatDuration(
      total / durations.length
    );
  }, [allDisputes]);

  const slaBreaches = useMemo(() => {
    return allDisputes.filter(
      (dispute) =>
        dispute.is_sla_breached === true
    ).length;
  }, [allDisputes]);

  const handleOpenDispute = (dispute) => {
    setSelectedDispute(dispute);
  };

  const handleCloseModal = () => {
    if (actionLoading) {
      return;
    }

    setSelectedDispute(null);
  };

  const handleMoveToReview = async () => {
    if (!selectedDispute) return;

    setActionLoading(true);
    setError('');

    try {
      await moveDisputeToReview(
        selectedDispute.id
      );

      setSelectedDispute(null);

      addToast({
        type: 'success',
        message:
          'Dispute moved to review successfully.',
      });

      await loadDisputes();
    } catch (err) {
      console.error(
        'Failed to move dispute to review:',
        err
      );

      const message = getErrorMessage(
        err,
        'Failed to move dispute to review.'
      );

      setError(message);

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleResolve = async (notes) => {
    if (
      !selectedDispute ||
      !notes ||
      !notes.trim()
    ) {
      return;
    }

    setActionLoading(true);
    setError('');

    try {
      await resolveDispute(
        selectedDispute.id,
        notes.trim()
      );

      setSelectedDispute(null);

      addToast({
        type: 'success',
        message:
          'Dispute resolved successfully.',
      });

      await loadDisputes();
    } catch (err) {
      console.error(
        'Failed to resolve dispute:',
        err
      );

      const message = getErrorMessage(
        err,
        'Failed to resolve dispute.'
      );

      setError(message);

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (notes) => {
    if (
      !selectedDispute ||
      !notes ||
      !notes.trim()
    ) {
      return;
    }

    setActionLoading(true);
    setError('');

    try {
      await rejectDispute(
        selectedDispute.id,
        notes.trim()
      );

      setSelectedDispute(null);

      addToast({
        type: 'success',
        message:
          'Dispute rejected successfully.',
      });

      await loadDisputes();
    } catch (err) {
      console.error(
        'Failed to reject dispute:',
        err
      );

      const message = getErrorMessage(
        err,
        'Failed to reject dispute.'
      );

      setError(message);

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-gray-50 p-4 sm:p-6">
      <div className="max-w-[1500px] mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-semibold text-gray-900">
            Disputes
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Manage payment disputes and monitor SLA status.
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-5 px-4 py-3 rounded-lg border border-red-200 bg-red-50 text-sm text-red-700"
            role="alert"
          >
            {error}
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <KPICard
            title="Total Disputes"
            value={
              loading
                ? '...'
                : allDisputes.length
            }
            trend="All disputes"
          />

          <KPICard
            title="Avg Resolution Time"
            value={
              loading
                ? '...'
                : averageResolutionTime
            }
            trend="Resolved / rejected"
          />

          <KPICard
            title="SLA Breaches"
            value={
              loading
                ? '...'
                : slaBreaches
            }
            trend="Backend-reported breaches"
          />
        </div>

        {/* Filter / Refresh */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div>
              <label
                htmlFor="dispute-status-filter"
                className="block text-sm font-medium text-gray-700"
              >
                Status
              </label>

              <select
                id="dispute-status-filter"
                value={filterStatus}
                onChange={(event) =>
                  setFilterStatus(
                    event.target.value
                  )
                }
                className="mt-1 w-full sm:w-52 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              >
                <option value="ALL">
                  All Statuses
                </option>

                {DISPUTE_STATUSES.map(
                  (status) => (
                    <option
                      key={status}
                      value={status}
                    >
                      {formatStatus(status)}
                    </option>
                  )
                )}
              </select>
            </div>

            <button
              type="button"
              onClick={loadDisputes}
              disabled={loading}
              className="sm:ml-auto self-end px-4 py-2 rounded-md border border-indigo-600 text-indigo-600 text-sm font-medium hover:bg-indigo-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? 'Refreshing...'
                : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Kanban */}
        {loading ? (
          <div className="bg-white border border-gray-200 rounded-lg min-h-[500px] flex items-center justify-center">
            <LoadingSpinner />
          </div>
        ) : allDisputes.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg">
            <EmptyState
              emoji="📋"
              title="No disputes found"
              description="There are currently no disputes available."
            />
          </div>
        ) : (
          <div className="overflow-x-auto pb-4">
            <div className="grid grid-cols-4 gap-4 min-w-[1200px]">
              {DISPUTE_STATUSES.map(
                (status) => (
                  <div
                    key={status}
                    className="bg-gray-100 border border-gray-200 rounded-lg p-3 min-h-[550px]"
                  >
                    {/* Column header */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <h2 className="text-sm font-semibold text-gray-800">
                          {formatStatus(status)}
                        </h2>

                        <span className="inline-flex items-center justify-center min-w-[24px] h-6 px-2 rounded-full bg-white border border-gray-200 text-xs font-semibold text-gray-600">
                          {
                            disputesByStatus[
                              status
                            ].length
                          }
                        </span>
                      </div>
                    </div>

                    {/* Cards */}
                    <div className="space-y-3 max-h-[700px] overflow-y-auto pr-1">
                      {disputesByStatus[
                        status
                      ].length === 0 ? (
                        <EmptyState
                          emoji="—"
                          title="No disputes"
                          description={`No ${formatStatus(
                            status
                          ).toLowerCase()} disputes.`}
                        />
                      ) : (
                        disputesByStatus[
                          status
                        ].map((dispute) => (
                          <DisputeCard
                            key={dispute.id}
                            dispute={dispute}
                            onClick={
                              handleOpenDispute
                            }
                          />
                        ))
                      )}
                    </div>
                  </div>
                )
              )}
            </div>
          </div>
        )}
      </div>

      {/* Dispute details / actions */}
      <Modal
        isOpen={Boolean(selectedDispute)}
        onClose={handleCloseModal}
      >
        {selectedDispute && (
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-1">
              Dispute Details
            </h2>

            <p className="text-xs text-gray-500 mb-5 break-all">
              {selectedDispute.id}
            </p>

            <DisputeDetails
              dispute={selectedDispute}
              onMoveToReview={
                handleMoveToReview
              }
              onResolve={handleResolve}
              onReject={handleReject}
              actionLoading={actionLoading}
            />
          </div>
        )}
      </Modal>
    </div>
  );
}

export default function Disputes() {
  return (
    <ToastProvider>
      <DisputesContent />
    </ToastProvider>
  );
}
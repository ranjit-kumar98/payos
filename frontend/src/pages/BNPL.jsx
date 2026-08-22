import React, { useEffect, useState } from 'react';
import {
  checkBnplEligibility,
  calculateBnpl,
  createBnplLoan,
  getBnplLoans,
} from '../api/client';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { formatIndianCurrency } from '../utils/formatters';
import { useToast, ToastProvider } from '../components/ToastProvider';

const TENURE_OPTIONS = [
  { months: 3, rate: 0.12 },
  { months: 6, rate: 0.14 },
  { months: 9, rate: 0.16 },
  { months: 12, rate: 0.18 },
];

function shortId(id) {
  if (!id) return 'N/A';
  return id.slice(0, 8);
}

function formatDate(date) {
  if (!date) return 'N/A';

  try {
    return new Date(date).toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'N/A';
  }
}

function statusClasses(status) {
  if (status === 'ACTIVE') {
    return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  }

  if (status === 'CLOSED') {
    return 'bg-gray-100 text-gray-700 border-gray-200';
  }

  if (status === 'DEFAULTED') {
    return 'bg-red-50 text-red-700 border-red-200';
  }

  return 'bg-gray-100 text-gray-700 border-gray-200';
}

function Metric({ label, value, highlight = false }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-400">
        {label}
      </p>

      <p
        className={`mt-1 ${
          highlight
            ? 'text-lg font-bold text-indigo-600'
            : 'text-lg font-bold text-gray-900'
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function BNPLContent() {
  const { addToast } = useToast();

  // ------------------------------------------------------------
  // Calculator
  // ------------------------------------------------------------

  const [principal, setPrincipal] = useState('');
  const [selectedTenure, setSelectedTenure] = useState(null);

  // ------------------------------------------------------------
  // Eligibility
  // ------------------------------------------------------------

  const [eligibilityLoading, setEligibilityLoading] = useState(false);
  const [eligibilityResult, setEligibilityResult] = useState(null);
  const [eligibilityError, setEligibilityError] = useState(null);

  // ------------------------------------------------------------
  // Calculation
  // ------------------------------------------------------------

  const [calculationLoading, setCalculationLoading] = useState(false);
  const [calculationResult, setCalculationResult] = useState(null);
  const [calculationError, setCalculationError] = useState(null);

  // ------------------------------------------------------------
  // Loan creation
  // ------------------------------------------------------------

  const [createLoading, setCreateLoading] = useState(false);
  const [createdLoan, setCreatedLoan] = useState(null);

  // ------------------------------------------------------------
  // Active loans
  // ------------------------------------------------------------

  const [loans, setLoans] = useState([]);
  const [loansLoading, setLoansLoading] = useState(false);
  const [loansError, setLoansError] = useState(null);

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------

  const [scheduleOpen, setScheduleOpen] = useState(false);

  // ------------------------------------------------------------
  // Initial load
  // ------------------------------------------------------------

  useEffect(() => {
    fetchLoans();
  }, []);

  // ------------------------------------------------------------
  // Fetch loans
  // ------------------------------------------------------------

  async function fetchLoans() {
    setLoansLoading(true);
    setLoansError(null);

    try {
      const response = await getBnplLoans();

      setLoans(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error('Failed to load BNPL loans:', err);

      setLoans([]);
      setLoansError('Failed to load your BNPL loans.');
    } finally {
      setLoansLoading(false);
    }
  }

  // ------------------------------------------------------------
  // Reset calculator after successful creation
  // ------------------------------------------------------------

  function handleCreateAnotherPlan() {
    setPrincipal('');
    setSelectedTenure(null);

    setEligibilityResult(null);
    setEligibilityError(null);

    setCalculationResult(null);
    setCalculationError(null);

    setCreatedLoan(null);
    setScheduleOpen(false);
  }

  // ------------------------------------------------------------
  // Amount change
  // ------------------------------------------------------------

  function handlePrincipalChange(event) {
    setPrincipal(event.target.value);

    // Changing the amount invalidates the previous calculation.
    setEligibilityResult(null);
    setEligibilityError(null);
    setCalculationResult(null);
    setCalculationError(null);
    setCreatedLoan(null);
    setScheduleOpen(false);
  }

  // ------------------------------------------------------------
  // Tenure change
  // ------------------------------------------------------------

  function handleTenureChange(option) {
    setSelectedTenure(option);

    // Changing tenure invalidates the previous calculation.
    setEligibilityResult(null);
    setEligibilityError(null);
    setCalculationResult(null);
    setCalculationError(null);
    setCreatedLoan(null);
    setScheduleOpen(false);
  }

  // ------------------------------------------------------------
  // Eligibility + calculation
  // ------------------------------------------------------------

  async function handleCheckEligibility() {
    setEligibilityError(null);
    setCalculationError(null);
    setEligibilityResult(null);
    setCalculationResult(null);
    setCreatedLoan(null);
    setScheduleOpen(false);

    const principalNum = Number(principal);

    if (!principalNum || principalNum <= 0) {
      setEligibilityError('Please enter a valid purchase amount.');
      return;
    }

    if (!selectedTenure) {
      setEligibilityError('Please select a repayment tenure.');
      return;
    }

    setEligibilityLoading(true);

    try {
      const response = await checkBnplEligibility(
        principalNum,
        selectedTenure.months
      );

      if (!response || typeof response.eligible !== 'boolean') {
        setEligibilityError('Invalid eligibility response from server.');
        return;
      }

      setEligibilityResult(response);

      // Not eligible → stop here.
      if (!response.eligible) {
        return;
      }

      // Eligible → calculate EMI.
      setCalculationLoading(true);

      try {
        const calculation = await calculateBnpl(
          principalNum,
          selectedTenure.months
        );

        setCalculationResult(calculation);
      } catch (err) {
        console.error('BNPL calculation failed:', err);

        const message =
          err?.response?.data?.detail ||
          err?.response?.data?.message ||
          'Failed to calculate EMI.';

        setCalculationError(message);
      } finally {
        setCalculationLoading(false);
      }
    } catch (err) {
      console.error('BNPL eligibility check failed:', err);

      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Failed to check BNPL eligibility.';

      setEligibilityError(message);
    } finally {
      setEligibilityLoading(false);
    }
  }

  // ------------------------------------------------------------
  // Create loan
  // ------------------------------------------------------------

  async function handleCreateLoan() {
    if (!calculationResult || !selectedTenure || createdLoan) {
      return;
    }

    setCreateLoading(true);

    try {
      const loan = await createBnplLoan(
        Number(principal),
        selectedTenure.months
      );

      // Keep the actual API response so the user can see
      // exactly which loan was created.
      setCreatedLoan(loan);

      // Close the repayment schedule after creation.
      setScheduleOpen(false);

      // Refresh the loan list.
      await fetchLoans();

      // Correct usage of the existing ToastProvider.
      addToast({
        type: 'success',
        message: 'BNPL loan created successfully.',
      });
    } catch (err) {
      console.error('BNPL loan creation failed:', err);

      const message =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        'Failed to create BNPL loan.';

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setCreateLoading(false);
    }
  }

  const checking =
    eligibilityLoading || calculationLoading;

  return (
    <div className="min-h-full bg-[#f6f7fb]">
      <div className="mx-auto w-full max-w-[1450px] px-5 py-6 lg:px-8 lg:py-8">

        {/* ======================================================
            PAGE HEADER
        ====================================================== */}

        <div className="mb-7">
          <div className="mb-2 flex items-center gap-2 text-xs font-medium text-gray-400">
            <span>PayOS</span>
            <span>/</span>
            <span className="text-gray-600">BNPL</span>
          </div>

          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h1 className="text-3xl font-bold tracking-tight text-gray-900">
                Buy Now, Pay Later
              </h1>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-500">
                Calculate your EMI, check eligibility, and manage your BNPL
                repayment plans from one place.
              </p>
            </div>

            <div className="flex gap-3">
              <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                  Available tenure
                </p>

                <p className="mt-1 text-sm font-bold text-gray-800">
                  3 / 6 / 9 / 12 months
                </p>
              </div>

              <div className="rounded-xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
                <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                  Total plans
                </p>

                <p className="mt-1 text-sm font-bold text-gray-800">
                  {loansLoading ? '—' : loans.length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ======================================================
            MAIN GRID
        ====================================================== */}

        <div className="grid grid-cols-1 gap-6 xl:grid-cols-[430px_minmax(0,1fr)]">

          {/* ====================================================
              LEFT: CALCULATOR
          ==================================================== */}

          <section className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">

            {/* Header */}

            <div className="border-b border-gray-100 px-6 py-5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-lg font-bold text-indigo-600">
                  ₹
                </div>

                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">
                    New plan
                  </p>

                  <h2 className="mt-0.5 text-lg font-bold text-gray-900">
                    BNPL EMI Calculator
                  </h2>

                  <p className="mt-1 text-xs text-gray-500">
                    Calculate before creating your loan.
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6">

              {/* Steps */}

              <div className="mb-7 flex items-center">
                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      principal
                        ? 'bg-indigo-600 text-white'
                        : 'bg-indigo-100 text-indigo-600'
                    }`}
                  >
                    1
                  </span>

                  <span className="hidden text-xs font-semibold text-gray-600 sm:block">
                    Amount
                  </span>
                </div>

                <div
                  className={`mx-2 h-px flex-1 ${
                    selectedTenure
                      ? 'bg-indigo-300'
                      : 'bg-gray-200'
                  }`}
                />

                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      selectedTenure
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    2
                  </span>

                  <span className="hidden text-xs font-semibold text-gray-600 sm:block">
                    Tenure
                  </span>
                </div>

                <div
                  className={`mx-2 h-px flex-1 ${
                    calculationResult
                      ? 'bg-indigo-300'
                      : 'bg-gray-200'
                  }`}
                />

                <div className="flex items-center gap-2">
                  <span
                    className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                      calculationResult
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                  >
                    3
                  </span>

                  <span className="hidden text-xs font-semibold text-gray-600 sm:block">
                    Review
                  </span>
                </div>
              </div>

              {/* Amount */}

              <label
                htmlFor="purchaseAmount"
                className="mb-2 block text-sm font-semibold text-gray-800"
              >
                Purchase amount
              </label>

              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-sm font-bold text-gray-500">
                  ₹
                </span>

                <input
                  id="purchaseAmount"
                  type="number"
                  min="0"
                  step="100"
                  value={principal}
                  onChange={handlePrincipalChange}
                  disabled={Boolean(createdLoan) || checking}
                  placeholder="Enter purchase amount"
                  className="w-full rounded-xl border border-gray-300 bg-white py-3.5 pl-9 pr-4 text-sm font-semibold text-gray-900 outline-none transition placeholder:text-gray-300 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-50 disabled:cursor-not-allowed disabled:bg-gray-100"
                />
              </div>

              <p className="mt-1.5 text-xs text-gray-400">
                Eligible range: ₹3,000 to ₹2,00,000
              </p>

              {/* Tenure */}

              <div className="mt-6">
                <p className="text-sm font-semibold text-gray-800">
                  Select repayment tenure
                </p>

                <p className="mt-1 text-xs text-gray-500">
                  Interest rate is fixed according to the selected tenure.
                </p>

                <div className="mt-3 grid grid-cols-2 gap-2.5">
                  {TENURE_OPTIONS.map((option) => {
                    const selected =
                      selectedTenure?.months === option.months;

                    return (
                      <button
                        key={option.months}
                        type="button"
                        disabled={Boolean(createdLoan) || checking}
                        onClick={() => handleTenureChange(option)}
                        className={`rounded-xl border px-3 py-3 text-left transition ${
                          selected
                            ? 'border-indigo-600 bg-indigo-600 text-white shadow-sm'
                            : 'border-gray-200 bg-white text-gray-700 hover:border-indigo-300 hover:bg-indigo-50'
                        } disabled:cursor-not-allowed disabled:opacity-60`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold">
                            {option.months} Months
                          </span>

                          {selected && (
                            <span className="text-xs font-bold">
                              ✓
                            </span>
                          )}
                        </div>

                        <p
                          className={`mt-1 text-xs ${
                            selected
                              ? 'text-indigo-100'
                              : 'text-gray-500'
                          }`}
                        >
                          {Math.round(option.rate * 100)}% p.a.
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Validation / API error */}

              {eligibilityError && (
                <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-bold text-red-800">
                    Unable to continue
                  </p>

                  <p className="mt-1 text-xs leading-5 text-red-700">
                    {eligibilityError}
                  </p>
                </div>
              )}

              {/* Check button */}

              {!createdLoan && (
                <button
                  type="button"
                  onClick={handleCheckEligibility}
                  disabled={checking}
                  className="mt-6 w-full rounded-xl bg-indigo-600 px-4 py-3.5 text-sm font-bold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {eligibilityLoading
                    ? 'Checking eligibility...'
                    : calculationLoading
                    ? 'Calculating EMI...'
                    : 'Check Eligibility'}
                </button>
              )}

              {/* Ineligible */}

              {eligibilityResult &&
                !eligibilityResult.eligible && (
                  <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4">
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 font-bold text-red-600">
                        ×
                      </div>

                      <div>
                        <p className="text-sm font-bold text-red-800">
                          BNPL not available
                        </p>

                        <p className="mt-1 text-xs leading-5 text-red-700">
                          {eligibilityResult.message}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

              {/* Calculation loading */}

              {calculationLoading && (
                <div className="mt-5 rounded-xl border border-gray-200 bg-gray-50 p-6 text-center">
                  <LoadingSpinner />

                  <p className="mt-3 text-xs text-gray-500">
                    Preparing your repayment plan...
                  </p>
                </div>
              )}

              {/* Calculation error */}

              {calculationError && (
                <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4">
                  <p className="text-sm font-bold text-red-800">
                    EMI calculation failed
                  </p>

                  <p className="mt-1 text-xs text-red-700">
                    {calculationError}
                  </p>
                </div>
              )}

              {/* =================================================
                  CALCULATION RESULT
              ================================================= */}

              {calculationResult && (
                <div className="mt-6 overflow-hidden rounded-2xl border border-indigo-100">

                  {/* Result heading */}

                  <div className="bg-indigo-50 px-5 py-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">
                          Eligible
                        </p>

                        <p className="mt-1 text-sm font-bold text-gray-900">
                          Your repayment plan
                        </p>
                      </div>

                      <span className="rounded-full bg-white px-3 py-1 text-xs font-bold text-indigo-700 shadow-sm">
                        {selectedTenure.months} Months
                      </span>
                    </div>
                  </div>

                  {/* Metrics */}

                  <div className="bg-white p-5">
                    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
                      <p className="text-xs font-semibold text-gray-500">
                        Monthly EMI
                      </p>

                      <p className="mt-1 text-3xl font-bold tracking-tight text-gray-900">
                        {formatIndianCurrency(
                          Number(calculationResult.monthly_emi)
                        )}
                      </p>

                      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                        <span>
                          {Math.round(
                            Number(
                              calculationResult.annual_interest_rate
                            ) * 100
                          )}
                          % p.a.
                        </span>

                        <span className="h-1 w-1 rounded-full bg-gray-300" />

                        <span>
                          {calculationResult.tenure} installments
                        </span>
                      </div>
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-3">
                      <div className="rounded-xl bg-gray-50 p-4">
                        <Metric
                          label="Total interest"
                          value={formatIndianCurrency(
                            Number(calculationResult.total_interest)
                          )}
                        />
                      </div>

                      <div className="rounded-xl bg-gray-50 p-4">
                        <Metric
                          label="Total payable"
                          value={formatIndianCurrency(
                            Number(calculationResult.total_repayment)
                          )}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Schedule */}

                  <div className="border-t border-gray-100 bg-white">
                    <button
                      type="button"
                      onClick={() =>
                        setScheduleOpen((previous) => !previous)
                      }
                      className="flex w-full items-center justify-between px-5 py-4 text-left transition hover:bg-gray-50"
                    >
                      <div>
                        <p className="text-sm font-bold text-gray-800">
                          Repayment schedule
                        </p>

                        <p className="mt-1 text-xs text-gray-500">
                          Monthly EMI, interest and principal breakdown
                        </p>
                      </div>

                      <span className="text-xs font-bold text-indigo-600">
                        {scheduleOpen ? 'Hide ↑' : 'View ↓'}
                      </span>
                    </button>

                    {scheduleOpen && (
                      <div className="border-t border-gray-100 p-4">
                        <div className="overflow-hidden rounded-xl border border-gray-200">
                          <div className="max-h-[280px] overflow-auto">
                            <table className="w-full min-w-[520px] text-xs">
                              <thead className="sticky top-0 bg-gray-50">
                                <tr>
                                  <th className="px-3 py-3 text-left font-bold text-gray-500">
                                    Month
                                  </th>

                                  <th className="px-3 py-3 text-right font-bold text-gray-500">
                                    EMI
                                  </th>

                                  <th className="px-3 py-3 text-right font-bold text-gray-500">
                                    Interest
                                  </th>

                                  <th className="px-3 py-3 text-right font-bold text-gray-500">
                                    Principal
                                  </th>

                                  <th className="px-3 py-3 text-right font-bold text-gray-500">
                                    Balance
                                  </th>
                                </tr>
                              </thead>

                              <tbody className="divide-y divide-gray-100">
                                {calculationResult.repayment_schedule?.map(
                                  (item) => (
                                    <tr key={item.month}>
                                      <td className="px-3 py-2.5 font-semibold text-gray-800">
                                        {item.month}
                                      </td>

                                      <td className="px-3 py-2.5 text-right">
                                        {formatIndianCurrency(
                                          Number(item.emi)
                                        )}
                                      </td>

                                      <td className="px-3 py-2.5 text-right">
                                        {formatIndianCurrency(
                                          Number(item.interest)
                                        )}
                                      </td>

                                      <td className="px-3 py-2.5 text-right">
                                        {formatIndianCurrency(
                                          Number(item.principal)
                                        )}
                                      </td>

                                      <td className="px-3 py-2.5 text-right font-semibold">
                                        {formatIndianCurrency(
                                          Number(item.remaining_balance)
                                        )}
                                      </td>
                                    </tr>
                                  )
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Create / success */}

                  <div className="border-t border-gray-100 bg-white p-4">
                    {createdLoan ? (
                      <div className="space-y-2">
                        <div className="flex items-center justify-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">
                          <span>✓</span>
                          Loan Created Successfully
                        </div>

                        <button
                          type="button"
                          onClick={handleCreateAnotherPlan}
                          className="w-full rounded-xl border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
                        >
                          Create Another Plan
                        </button>
                      </div>
                    ) : (
                      <button
                        type="button"
                        onClick={handleCreateLoan}
                        disabled={createLoading}
                        className="w-full rounded-xl bg-gray-900 px-4 py-3.5 text-sm font-bold text-white transition hover:bg-gray-800 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {createLoading
                          ? 'Creating Loan...'
                          : 'Create BNPL Loan'}
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Created loan details */}

              {createdLoan && (
                <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/50 p-4">
                  <p className="text-[10px] font-bold uppercase tracking-widest text-emerald-600">
                    Created Loan ID
                  </p>

                  <p className="mt-1 break-all font-mono text-xs font-semibold text-emerald-800">
                    {createdLoan.id}
                  </p>

                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] font-semibold uppercase text-emerald-600">
                        Principal
                      </p>

                      <p className="mt-1 text-sm font-bold text-emerald-900">
                        {formatIndianCurrency(
                          Number(createdLoan.principal)
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-[10px] font-semibold uppercase text-emerald-600">
                        Monthly EMI
                      </p>

                      <p className="mt-1 text-sm font-bold text-emerald-900">
                        {formatIndianCurrency(
                          Number(createdLoan.monthly_emi)
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* ====================================================
              RIGHT: LOANS
          ==================================================== */}

          <section className="min-w-0 overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">

            {/* Header */}

            <div className="border-b border-gray-100 px-6 py-5">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-widest text-indigo-600">
                    Portfolio
                  </p>

                  <h2 className="mt-1 text-lg font-bold text-gray-900">
                    BNPL Loans
                  </h2>

                  <p className="mt-1 text-xs text-gray-500">
                    Your existing repayment plans and their current status.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={fetchLoans}
                  disabled={loansLoading}
                  className="self-start rounded-lg border border-gray-200 bg-white px-3 py-2 text-xs font-semibold text-gray-600 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loansLoading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
            </div>

            <div className="p-5 sm:p-6">

              {/* Loading */}

              {loansLoading && (
                <div className="flex min-h-[300px] items-center justify-center">
                  <div className="text-center">
                    <LoadingSpinner />

                    <p className="mt-3 text-xs text-gray-500">
                      Loading your BNPL loans...
                    </p>
                  </div>
                </div>
              )}

              {/* Error */}

              {!loansLoading && loansError && (
                <div className="flex min-h-[300px] items-center justify-center">
                  <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-center">
                    <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-red-100 font-bold text-red-600">
                      !
                    </div>

                    <p className="mt-3 text-sm font-bold text-red-800">
                      Unable to load loans
                    </p>

                    <p className="mt-1 text-xs text-red-700">
                      {loansError}
                    </p>

                    <button
                      type="button"
                      onClick={fetchLoans}
                      className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-xs font-bold text-white hover:bg-red-700"
                    >
                      Try Again
                    </button>
                  </div>
                </div>
              )}

              {/* Empty */}

              {!loansLoading &&
                !loansError &&
                loans.length === 0 && (
                  <div className="flex min-h-[300px] items-center justify-center">
                    <EmptyState message="No BNPL loans found." />
                  </div>
                )}

              {/* Loan cards */}

              {!loansLoading &&
                !loansError &&
                loans.length > 0 && (
                  <div className="space-y-4">
                    {loans.map((loan) => (
                      <article
                        key={loan.id}
                        className="overflow-hidden rounded-2xl border border-gray-200 bg-white transition hover:border-indigo-200 hover:shadow-sm"
                      >

                        {/* Loan heading */}

                        <div className="flex flex-col gap-3 border-b border-gray-100 bg-gray-50/60 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-indigo-50 font-bold text-indigo-600">
                              ₹
                            </div>

                            <div>
                              <div className="flex items-center gap-2">
                                <p className="text-sm font-bold text-gray-900">
                                  BNPL Loan
                                </p>

                                <span
                                  className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${statusClasses(
                                    loan.status
                                  )}`}
                                >
                                  {loan.status}
                                </span>
                              </div>

                              <p className="mt-1 font-mono text-[11px] text-gray-400">
                                #{shortId(loan.id)}
                              </p>
                            </div>
                          </div>

                          <div className="sm:text-right">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Created
                            </p>

                            <p className="mt-1 text-xs font-semibold text-gray-600">
                              {formatDate(loan.created_at)}
                            </p>
                          </div>
                        </div>

                        {/* Primary values */}

                        <div className="grid grid-cols-1 divide-y divide-gray-100 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                          <div className="p-4">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Principal
                            </p>

                            <p className="mt-1 text-xl font-bold text-gray-900">
                              {formatIndianCurrency(
                                Number(loan.principal)
                              )}
                            </p>
                          </div>

                          <div className="p-4">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Monthly EMI
                            </p>

                            <p className="mt-1 text-xl font-bold text-indigo-600">
                              {formatIndianCurrency(
                                Number(loan.monthly_emi)
                              )}
                            </p>
                          </div>

                          <div className="p-4">
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Total Payable
                            </p>

                            <p className="mt-1 text-xl font-bold text-gray-900">
                              {formatIndianCurrency(
                                Number(loan.total_repayment)
                              )}
                            </p>
                          </div>
                        </div>

                        {/* Secondary details */}

                        <div className="grid grid-cols-2 gap-y-4 border-t border-gray-100 px-5 py-4 sm:grid-cols-4">
                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Tenure
                            </p>

                            <p className="mt-1 text-sm font-bold text-gray-800">
                              {loan.tenure_months} months
                            </p>
                          </div>

                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Interest Rate
                            </p>

                            <p className="mt-1 text-sm font-bold text-gray-800">
                              {Math.round(
                                Number(loan.annual_interest_rate) * 100
                              )}
                              % p.a.
                            </p>
                          </div>

                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Total Interest
                            </p>

                            <p className="mt-1 text-sm font-bold text-gray-800">
                              {formatIndianCurrency(
                                Number(loan.total_interest)
                              )}
                            </p>
                          </div>

                          <div>
                            <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                              Loan ID
                            </p>

                            <p className="mt-1 font-mono text-sm font-bold text-gray-800">
                              {shortId(loan.id)}
                            </p>
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

export default function BNPL() {
  return (
    <ToastProvider>
      <BNPLContent />
    </ToastProvider>
  );
}
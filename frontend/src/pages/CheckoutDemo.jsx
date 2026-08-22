import React, { useState } from 'react';
import { routePayment, createPaymentOrder } from '../api/client';
import { ToastProvider, useToast } from '../components/ToastProvider';

const PRODUCT_NAME = 'PayOS Pro';
const PRODUCT_AMOUNT = 4999;
const PRODUCT_CURRENCY = 'INR';

const STEP = {
  INITIAL: 'INITIAL',
  GATEWAY_SELECTED: 'GATEWAY_SELECTED',
  PAYMENT_IN_PROGRESS: 'PAYMENT_IN_PROGRESS',
  SUCCESS: 'SUCCESS',
  FAILED: 'FAILED',
};

function CheckoutDemoContent() {
  const { addToast } = useToast();

  // ------------------------------------------------------------
  // State
  // ------------------------------------------------------------

  const [step, setStep] = useState(STEP.INITIAL);

  const [gatewayData, setGatewayData] = useState(null);

  const [paymentLoading, setPaymentLoading] = useState(false);

  const [paymentResult, setPaymentResult] = useState(null);

  const [paymentError, setPaymentError] = useState(null);

  // ------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------

  const formatCurrency = (amount) => {
    return `₹${Number(amount).toLocaleString('en-IN', {
      maximumFractionDigits: 2,
    })}`;
  };

  const getErrorMessage = (error, fallback) => {
    return (
      error?.response?.data?.detail ||
      error?.response?.data?.message ||
      error?.message ||
      fallback
    );
  };

  const isRazorpayGateway =
    gatewayData?.selected_gateway?.toLowerCase() === 'razorpay';

  // ------------------------------------------------------------
  // Load Razorpay SDK
  // ------------------------------------------------------------

  const loadRazorpayScript = () => {
    return new Promise((resolve, reject) => {
      if (window.Razorpay) {
        resolve(true);
        return;
      }

      const existingScript = document.querySelector(
        'script[src="https://checkout.razorpay.com/v1/checkout.js"]'
      );

      if (existingScript) {
        existingScript.addEventListener('load', () => resolve(true));
        existingScript.addEventListener(
          'error',
          () => reject(new Error('Failed to load Razorpay SDK'))
        );
        return;
      }

      const script = document.createElement('script');

      script.src = 'https://checkout.razorpay.com/v1/checkout.js';
      script.async = true;

      script.onload = () => resolve(true);

      script.onerror = () => {
        reject(new Error('Failed to load Razorpay SDK'));
      };

      document.body.appendChild(script);
    });
  };

  // ------------------------------------------------------------
  // Step 1: Find best gateway
  // ------------------------------------------------------------

  const findBestGateway = async () => {
    setPaymentLoading(true);
    setPaymentError(null);
    setPaymentResult(null);

    try {
      const data = await routePayment(
        PRODUCT_AMOUNT,
        PRODUCT_CURRENCY,
        'CARD'
      );

      setGatewayData(data);
      setStep(STEP.GATEWAY_SELECTED);

      addToast({
        type: 'success',
        message: 'Best payment gateway selected.',
      });
    } catch (error) {
      const message = getErrorMessage(
        error,
        'Failed to find the best payment gateway.'
      );

      setPaymentError(message);

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setPaymentLoading(false);
    }
  };

  // ------------------------------------------------------------
  // Step 2: Create Razorpay order + open checkout
  // ------------------------------------------------------------

  const handleRazorpayPayment = async () => {
    if (!gatewayData) {
      addToast({
        type: 'error',
        message: 'Please select a payment gateway first.',
      });
      return;
    }

    if (!isRazorpayGateway) {
      addToast({
        type: 'error',
        message: 'Razorpay is not the selected gateway.',
      });
      return;
    }

    setPaymentLoading(true);
    setPaymentError(null);
    setPaymentResult(null);

    setStep(STEP.PAYMENT_IN_PROGRESS);

    try {
      // Load Razorpay Checkout SDK
      await loadRazorpayScript();

      // Create PayOS/Razorpay order through backend
      const orderData = await createPaymentOrder(
        PRODUCT_AMOUNT,
        PRODUCT_CURRENCY,
        'CARD'
      );

      if (!orderData?.key_id || !orderData?.order_id) {
        throw new Error(
          'Payment order was created but Razorpay key/order information is missing.'
        );
      }

      const options = {
        key: orderData.key_id,

        order_id: orderData.order_id,

        amount: PRODUCT_AMOUNT * 100,

        currency: PRODUCT_CURRENCY,

        name: PRODUCT_NAME,

        description: 'PayOS Test Mode Payment',

        // --------------------------------------------------------
        // Razorpay successful payment callback
        // --------------------------------------------------------

        handler: function (response) {
          setPaymentResult({
            success: true,
            payment_id: response.razorpay_payment_id,
            order_id: response.razorpay_order_id,
            signature: response.razorpay_signature,
          });

          setStep(STEP.SUCCESS);

          addToast({
            type: 'success',
            message: 'Razorpay payment completed successfully.',
          });
        },

        // --------------------------------------------------------
        // Razorpay popup dismissal
        // --------------------------------------------------------

        modal: {
          ondismiss: function () {
            setPaymentResult({
              success: false,
              message: 'Payment popup was closed before completion.',
            });

            setStep(STEP.FAILED);

            addToast({
              type: 'error',
              message: 'Payment popup closed.',
            });
          },
        },

        // --------------------------------------------------------
        // Checkout preferences
        // --------------------------------------------------------

        prefill: {
          name: 'PayOS Test Customer',
        },

        notes: {
          product: PRODUCT_NAME,
          environment: 'TEST',
        },

        theme: {
          color: '#4f46e5',
        },
      };

      const razorpay = new window.Razorpay(options);

      // ----------------------------------------------------------
      // Razorpay payment failure
      // ----------------------------------------------------------

      razorpay.on('payment.failed', function (response) {
        const description =
          response?.error?.description ||
          'The Razorpay payment could not be completed.';

        setPaymentResult({
          success: false,
          message: description,
          code: response?.error?.code,
          reason: response?.error?.reason,
          source: response?.error?.source,
          step: response?.error?.step,
        });

        setStep(STEP.FAILED);

        addToast({
          type: 'error',
          message: `Payment failed: ${description}`,
        });
      });

      // Open actual Razorpay checkout
      razorpay.open();
    } catch (error) {
      const message = getErrorMessage(
        error,
        'Failed to initiate the payment.'
      );

      setPaymentError(message);

      setPaymentResult({
        success: false,
        message,
      });

      setStep(STEP.FAILED);

      addToast({
        type: 'error',
        message,
      });
    } finally {
      setPaymentLoading(false);
    }
  };

  // ------------------------------------------------------------
  // Reset everything
  // ------------------------------------------------------------

  const resetPayment = () => {
    setStep(STEP.INITIAL);
    setGatewayData(null);
    setPaymentResult(null);
    setPaymentError(null);
    setPaymentLoading(false);
  };

  // ------------------------------------------------------------
  // Step indicator
  // ------------------------------------------------------------

  const stepItems = [
    {
      label: 'Product',
      active: step === STEP.INITIAL,
      completed:
        step !== STEP.INITIAL,
    },
    {
      label: 'Gateway',
      active: step === STEP.GATEWAY_SELECTED,
      completed:
        step === STEP.PAYMENT_IN_PROGRESS ||
        step === STEP.SUCCESS ||
        step === STEP.FAILED,
    },
    {
      label: 'Payment',
      active: step === STEP.PAYMENT_IN_PROGRESS,
      completed:
        step === STEP.SUCCESS ||
        step === STEP.FAILED,
    },
    {
      label: 'Result',
      active:
        step === STEP.SUCCESS ||
        step === STEP.FAILED,
      completed: false,
    },
  ];

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------

  return (
    <div className="min-h-full bg-gray-50 px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">

        {/* ---------------------------------------------------- */}
        {/* Header */}
        {/* ---------------------------------------------------- */}

        <div className="mb-6">
          <div className="mb-1 text-sm font-medium text-indigo-600">
            PayOS / Checkout Demo
          </div>

          <h1 className="text-3xl font-bold tracking-tight text-gray-900">
            Test Checkout
          </h1>

          <p className="mt-1 text-sm text-gray-500">
            Test the complete PayOS payment routing and Razorpay checkout
            flow.
          </p>
        </div>

        {/* ---------------------------------------------------- */}
        {/* Main layout */}
        {/* ---------------------------------------------------- */}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">

          {/* ================================================== */}
          {/* Product card */}
          {/* ================================================== */}

          <section className="lg:col-span-2">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">

              <div className="border-b border-gray-100 px-6 py-5">
                <div className="mb-2 flex items-center justify-between">
                  <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-600">
                    Test Product
                  </span>

                  <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">
                    TEST MODE
                  </span>
                </div>

                <h2 className="text-2xl font-bold text-gray-900">
                  {PRODUCT_NAME}
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Premium PayOS checkout demonstration product.
                </p>
              </div>

              <div className="px-6 py-6">

                <div className="rounded-xl bg-gray-50 p-5">
                  <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
                    Amount
                  </div>

                  <div className="mt-2 text-4xl font-bold text-gray-900">
                    {formatCurrency(PRODUCT_AMOUNT)}
                  </div>

                  <div className="mt-1 text-sm text-gray-500">
                    {PRODUCT_CURRENCY}
                  </div>
                </div>

                <div className="mt-5 space-y-3 text-sm">

                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">
                      Product
                    </span>

                    <span className="font-medium text-gray-900">
                      {PRODUCT_NAME}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">
                      Payment method
                    </span>

                    <span className="font-medium text-gray-900">
                      Card
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">
                      Currency
                    </span>

                    <span className="font-medium text-gray-900">
                      INR
                    </span>
                  </div>

                </div>

                <div className="mt-6 rounded-xl border border-amber-200 bg-amber-50 p-4">
                  <div className="flex gap-3">
                    <div className="text-amber-600">
                      ⚠
                    </div>

                    <div>
                      <div className="text-sm font-semibold text-amber-800">
                        Test mode only
                      </div>

                      <p className="mt-1 text-xs leading-5 text-amber-700">
                        This checkout uses Razorpay test mode. No real
                        money should be charged.
                      </p>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          </section>

          {/* ================================================== */}
          {/* Payment flow */}
          {/* ================================================== */}

          <section className="lg:col-span-3">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-sm">

              <div className="border-b border-gray-100 px-6 py-5">
                <h2 className="text-xl font-bold text-gray-900">
                  Payment Flow
                </h2>

                <p className="mt-1 text-sm text-gray-500">
                  Route the payment and complete it using Razorpay.
                </p>
              </div>

              <div className="px-6 py-6">

                {/* ------------------------------------------------ */}
                {/* Step indicator */}
                {/* ------------------------------------------------ */}

                <div className="mb-8 grid grid-cols-4 gap-2">

                  {stepItems.map((item, index) => (
                    <div key={item.label} className="relative">

                      <div className="flex flex-col items-center">

                        <div
                          className={[
                            'flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold transition',
                            item.active
                              ? 'bg-indigo-600 text-white'
                              : item.completed
                                ? 'bg-indigo-100 text-indigo-700'
                                : 'bg-gray-100 text-gray-400',
                          ].join(' ')}
                        >
                          {item.completed ? '✓' : index + 1}
                        </div>

                        <span
                          className={[
                            'mt-2 text-center text-xs font-medium',
                            item.active
                              ? 'text-indigo-600'
                              : item.completed
                                ? 'text-gray-700'
                                : 'text-gray-400',
                          ].join(' ')}
                        >
                          {item.label}
                        </span>
                      </div>

                      {index < stepItems.length - 1 && (
                        <div
                          className={[
                            'absolute left-[calc(50%+18px)] right-[calc(-50%+18px)] top-4 h-px',
                            item.completed
                              ? 'bg-indigo-300'
                              : 'bg-gray-200',
                          ].join(' ')}
                        />
                      )}

                    </div>
                  ))}

                </div>

                {/* ================================================= */}
                {/* STEP 1 */}
                {/* ================================================= */}

                {step === STEP.INITIAL && (
                  <div className="rounded-xl border border-gray-200 bg-gray-50 p-5">

                    <div className="mb-5">
                      <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                        Step 1
                      </div>

                      <h3 className="mt-1 text-lg font-bold text-gray-900">
                        Find the best gateway
                      </h3>

                      <p className="mt-1 text-sm text-gray-500">
                        PayOS will select the best available gateway for
                        this payment method.
                      </p>
                    </div>

                    <button
                      type="button"
                      onClick={findBestGateway}
                      disabled={paymentLoading}
                      className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {paymentLoading
                        ? 'Finding Best Gateway...'
                        : 'Find Best Gateway'}
                    </button>

                    {paymentError && (
                      <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        {paymentError}
                      </div>
                    )}

                  </div>
                )}

                {/* ================================================= */}
                {/* STEP 2 */}
                {/* ================================================= */}

                {step === STEP.GATEWAY_SELECTED && gatewayData && (
                  <div className="space-y-5">

                    <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-5">

                      <div className="mb-4">
                        <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                          Step 2
                        </div>

                        <h3 className="mt-1 text-lg font-bold text-gray-900">
                          Gateway selected
                        </h3>
                      </div>

                      <div className="space-y-3">

                        <div className="flex items-center justify-between rounded-lg bg-white p-3">
                          <span className="text-sm text-gray-500">
                            Selected gateway
                          </span>

                          <span className="font-semibold text-gray-900">
                            {gatewayData.selected_gateway}
                          </span>
                        </div>

                        <div className="flex items-center justify-between rounded-lg bg-white p-3">
                          <span className="text-sm text-gray-500">
                            Backup gateway
                          </span>

                          <span className="font-semibold text-gray-900">
                            {gatewayData.backup_gateway || 'None'}
                          </span>
                        </div>

                        <div className="flex items-center justify-between rounded-lg bg-white p-3">
                          <span className="text-sm text-gray-500">
                            Estimated fee
                          </span>

                          <span className="font-semibold text-gray-900">
                            {formatCurrency(gatewayData.estimated_fee)}
                          </span>
                        </div>

                      </div>

                      {gatewayData.selection_reason && (
                        <div className="mt-4 text-xs leading-5 text-indigo-700">
                          <span className="font-semibold">
                            Why this gateway?
                          </span>{' '}
                          {gatewayData.selection_reason}
                        </div>
                      )}

                    </div>

                    {isRazorpayGateway ? (
                      <div className="rounded-xl border border-gray-200 bg-white p-5">

                        <div className="mb-4">
                          <div className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
                            Step 3
                          </div>

                          <h3 className="mt-1 text-lg font-bold text-gray-900">
                            Pay with Razorpay
                          </h3>

                          <p className="mt-1 text-sm text-gray-500">
                            You will be redirected to the Razorpay test
                            checkout popup.
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={handleRazorpayPayment}
                          disabled={paymentLoading}
                          className="w-full rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {paymentLoading
                            ? 'Opening Razorpay...'
                            : `Pay ${formatCurrency(PRODUCT_AMOUNT)} with Razorpay`}
                        </button>

                      </div>
                    ) : (
                      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                        Razorpay is not the selected gateway for this
                        payment.
                      </div>
                    )}

                  </div>
                )}

                {/* ================================================= */}
                {/* STEP 3 */}
                {/* ================================================= */}

                {step === STEP.PAYMENT_IN_PROGRESS && (
                  <div className="rounded-xl border border-indigo-100 bg-indigo-50 p-8 text-center">

                    <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-indigo-100 text-indigo-600">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" />
                    </div>

                    <div className="text-lg font-bold text-gray-900">
                      Preparing payment...
                    </div>

                    <p className="mt-2 text-sm text-gray-500">
                      Creating your Razorpay order and opening the
                      secure checkout.
                    </p>

                  </div>
                )}

                {/* ================================================= */}
                {/* STEP 4 - SUCCESS */}
                {/* ================================================= */}

                {step === STEP.SUCCESS && paymentResult && (
                  <div className="space-y-5">

                    <div className="rounded-xl border border-green-200 bg-green-50 p-6">

                      <div className="mb-4 flex items-center gap-3">

                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-100 text-lg text-green-700">
                          ✓
                        </div>

                        <div>
                          <div className="text-lg font-bold text-green-800">
                            Payment Successful
                          </div>

                          <div className="text-sm text-green-700">
                            Razorpay accepted the payment.
                          </div>
                        </div>

                      </div>

                      <div className="space-y-3 rounded-lg bg-white p-4">

                        <div>
                          <div className="text-xs font-medium uppercase tracking-wide text-gray-400">
                            Payment ID
                          </div>

                          <div className="mt-1 break-all text-sm font-semibold text-gray-900">
                            {paymentResult.payment_id}
                          </div>
                        </div>

                        <div>
                          <div className="text-xs font-medium uppercase tracking-wide text-gray-400">
                            Razorpay Order ID
                          </div>

                          <div className="mt-1 break-all text-sm font-semibold text-gray-900">
                            {paymentResult.order_id}
                          </div>
                        </div>

                      </div>

                    </div>

                    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 text-xs leading-5 text-blue-700">
                      PayOS transaction status is finalized by the
                      backend payment/webhook flow. This screen displays
                      the payment identifiers returned by Razorpay and
                      does not fabricate a PayOS transaction ID.
                    </div>

                    <button
                      type="button"
                      onClick={resetPayment}
                      className="w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
                    >
                      New Payment
                    </button>

                  </div>
                )}

                {/* ================================================= */}
                {/* STEP 4 - FAILED */}
                {/* ================================================= */}

                {step === STEP.FAILED && paymentResult && (
                  <div className="space-y-5">

                    <div className="rounded-xl border border-red-200 bg-red-50 p-6">

                      <div className="mb-4 flex items-center gap-3">

                        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-red-100 text-lg text-red-700">
                          !
                        </div>

                        <div>
                          <div className="text-lg font-bold text-red-800">
                            Payment Failed
                          </div>

                          <div className="text-sm text-red-700">
                            The payment was not completed.
                          </div>
                        </div>

                      </div>

                      <div className="rounded-lg bg-white p-4">

                        <div className="text-xs font-medium uppercase tracking-wide text-gray-400">
                          Reason
                        </div>

                        <div className="mt-1 text-sm font-medium text-gray-900">
                          {paymentResult.message ||
                            'Payment was not successful.'}
                        </div>

                      </div>

                    </div>

                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">

                      <button
                        type="button"
                        onClick={handleRazorpayPayment}
                        disabled={paymentLoading}
                        className="rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {paymentLoading
                          ? 'Retrying...'
                          : 'Retry Payment'}
                      </button>

                      <button
                        type="button"
                        onClick={resetPayment}
                        className="rounded-lg border border-gray-300 bg-white px-4 py-3 text-sm font-semibold text-gray-700 transition hover:bg-gray-50"
                      >
                        New Payment
                      </button>

                    </div>

                  </div>
                )}

              </div>
            </div>
          </section>
        </div>

        {/* ---------------------------------------------------- */}
        {/* Footer disclaimer */}
        {/* ---------------------------------------------------- */}

        <div className="mt-5 text-center text-xs text-gray-400">
          PayOS Checkout Demo · Razorpay test mode · No real payment
          should be processed
        </div>

      </div>
    </div>
  );
}

// IMPORTANT:
// CheckoutDemoContent uses useToast(), therefore it MUST be rendered
// inside ToastProvider.
//
// Keeping the provider here makes this page self-contained and avoids
// changing App.jsx/AppShell.jsx or disturbing the already-working BNPL
// toast implementation.
export default function CheckoutDemo() {
  return (
    <ToastProvider>
      <CheckoutDemoContent />
    </ToastProvider>
  );
}
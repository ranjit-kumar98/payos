import { useEffect, useRef } from 'react';

const WS_URL = 'ws://localhost/ws';

export function useWebSocket({
  onPaymentSuccess,
  onFraudDetected,
}) {
  const socketRef = useRef(null);

  const paymentSuccessRef = useRef(onPaymentSuccess);
  const fraudDetectedRef = useRef(onFraudDetected);

  useEffect(() => {
    paymentSuccessRef.current = onPaymentSuccess;
  }, [onPaymentSuccess]);

  useEffect(() => {
    fraudDetectedRef.current = onFraudDetected;
  }, [onFraudDetected]);

  useEffect(() => {
  let isUnmounting = false;

  const socket = new WebSocket(WS_URL);

  socketRef.current = socket;

  socket.onopen = () => {
    if (!isUnmounting) {
      console.log('WebSocket connected:', WS_URL);
    }
  };

  socket.onmessage = (event) => {
    if (isUnmounting) {
      return;
    }

    try {
      const message = JSON.parse(event.data);

      console.log('WebSocket message:', message);

      if (
        message.type === 'payment.success' &&
        paymentSuccessRef.current
      ) {
        paymentSuccessRef.current(message);
      }

      if (
        message.type === 'fraud.detected' &&
        fraudDetectedRef.current
      ) {
        fraudDetectedRef.current(message);
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  socket.onerror = (error) => {
    // Ignore errors caused by React StrictMode cleanup/unmount.
    if (!isUnmounting) {
      console.error('WebSocket error:', error);
    }
  };

  socket.onclose = (event) => {
    if (!isUnmounting) {
      console.log(
        'WebSocket disconnected:',
        event.code,
        event.reason || 'No reason provided'
      );
    }
  };

  return () => {
    isUnmounting = true;

    if (
      socket.readyState === WebSocket.OPEN ||
      socket.readyState === WebSocket.CONNECTING
    ) {
      socket.close();
    }

    if (socketRef.current === socket) {
      socketRef.current = null;
    }
  };
}, []);

  return socketRef;
}
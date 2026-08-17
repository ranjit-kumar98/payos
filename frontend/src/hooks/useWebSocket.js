import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

export function useWebSocket({ onPaymentSuccess, onFraudDetected }) {
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io(import.meta.env.VITE_API_URL, {
      path: '/socket.io',
    });
    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('payment.success', (data) => {
      if (onPaymentSuccess) onPaymentSuccess(data);
    });

    socket.on('fraud.detected', (data) => {
      if (onFraudDetected) onFraudDetected(data);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    return () => {
      socket.off('payment.success');
      socket.off('fraud.detected');
      socket.disconnect();
    };
  }, [onPaymentSuccess, onFraudDetected]);
}
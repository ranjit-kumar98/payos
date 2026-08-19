import { useEffect, useRef } from 'react';

export function useWebSocket({ onPaymentSuccess, onFraudDetected }) {
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = new WebSocket('ws://localhost:3001/ws');
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'payment.success' && onPaymentSuccess) {
          onPaymentSuccess(message);
        } else if (message.type === 'fraud.detected' && onFraudDetected) {
          onFraudDetected(message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    socket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [onPaymentSuccess, onFraudDetected]);
}
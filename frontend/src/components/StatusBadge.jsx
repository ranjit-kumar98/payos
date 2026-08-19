import React from 'react';

const statusStyles = {
  PENDING: 'bg-yellow-100 text-yellow-800',
  SUCCESS: 'bg-green-600 text-white',
  FAILED: 'bg-red-600 text-white',
  BLOCKED: 'bg-red-800 text-white',
  REFUNDED: 'bg-blue-600 text-white',
};

export function StatusBadge({ status }) {
  const style = statusStyles[status] || 'bg-gray-200 text-gray-800';
  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold ${style}`}
    >
      {status}
    </span>
  );
}

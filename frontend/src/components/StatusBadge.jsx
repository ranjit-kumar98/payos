import React from 'react';
import { statusToColor } from '../utils/formatters';

export function StatusBadge({ status }) {
  const color = statusToColor(status);
  return (

    <span
      className={`inline-block px-3 py-1 rounded-full text-white text-xs font-semibold bg-${color}-500`}
    >
      {status}
    </span>
  );
}

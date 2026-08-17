import React from 'react';
import { riskScoreToColor } from '../utils/formatters';

export function RiskBadge({ score }) {
  const color = riskScoreToColor(score);
  const isHighRisk = score > 85;

  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-white text-xs font-semibold bg-${color}-500 ${isHighRisk ? 'animate-pulse' : ''}`}
    >
      Risk: {score}
    </span>
  );
}

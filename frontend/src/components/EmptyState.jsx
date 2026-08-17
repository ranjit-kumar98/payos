import React from 'react';

export function EmptyState({ emoji, title, description }) {
  return (
    <div className="text-center p-8">
      <div className="text-6xl mb-4">{emoji}</div>
      <h2 className="text-xl font-semibold mb-2">{title}</h2>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
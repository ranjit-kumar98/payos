import React from 'react';

export function KPICard({ title, value, icon, trend }) {
  return (
    <div className="p-4 bg-white rounded shadow flex items-center space-x-4">
      {icon && <div className="text-blue-500">{icon}</div>}
      <div>
        <div className="text-sm font-medium text-gray-500">{title}</div>
        <div className="text-2xl font-semibold">{value}</div>
        {trend && <div className="text-sm text-gray-400">{trend}</div>}
      </div>
    </div>
  );
}
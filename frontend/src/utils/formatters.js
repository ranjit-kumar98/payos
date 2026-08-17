// Indian currency formatter with compact notation for large numbers
export function formatIndianCurrency(amount) {
  if (amount === null || amount === undefined) return '';
  const absAmount = Math.abs(amount);
  if (absAmount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(1)}Cr`;
  } else if (absAmount >= 100000) {
    return `₹${(amount / 100000).toFixed(1)}L`;
  } else {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  }
}

// Date formatter for IST timezone
export function formatDateIST(dateString) {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('en-IN', {
    timeZone: 'Asia/Kolkata',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Risk score to color mapping
export function riskScoreToColor(score) {
  if (score <= 30) return 'green';
  if (score <= 70) return 'yellow';
  return 'red';
}

// Status to color mapping
const statusColorMap = {
  pending: 'gray',
  approved: 'green',
  rejected: 'red',
  failed: 'red',
  success: 'green',
  processing: 'yellow',
  // Add more statuses as needed
};

export function statusToColor(status) {
  if (!status) return 'gray';
  return statusColorMap[status.toLowerCase()] || 'gray';
}
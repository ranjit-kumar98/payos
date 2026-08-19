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
export function formatDateTimeIST(utcString) {
  if (!utcString) return '';
  try {
    const date = new Date(utcString);
    // Convert to IST offset +5:30
    const istOffset = 5 * 60 + 30;
    const utc = date.getTime() + date.getTimezoneOffset() * 60000;
    const istTime = new Date(utc + istOffset * 60000);

    const options = {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    };
    return istTime.toLocaleString('en-IN', options);
  } catch {
    return utcString;
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

const statusColorMap = {
  pending: 'gray',
  approved: 'green',
  rejected: 'red',
  failed: 'red',
  success: 'green',
  processing: 'yellow',
  refunded: 'blue',
  // Add more statuses as needed
};

export function statusToColor(status) {
  if (!status) return 'gray';
  return statusColorMap[status.toLowerCase()] || 'gray';
}

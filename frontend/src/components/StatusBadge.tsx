

interface Props {
  status: string;
}

export default function StatusBadge({ status }: Props) {
  const s = (status || '').toLowerCase();
  
  let className = 'badge badge-pending';
  
  if (s === 'approved' || s === 'completed' || s === 'success') {
    className = 'badge badge-approved';
  } else if (s === 'denied' || s === 'failed' || s === 'error') {
    className = 'badge badge-denied';
  } else if (s === 'escalated') {
    className = 'badge badge-escalated';
  } else if (s === 'flagged') {
    className = 'badge badge-flagged';
  } else if (s === 'clarification') {
    className = 'badge badge-clarification';
  }

  return (
    <span className={className}>
      {status}
    </span>
  );
}


export default function StatusBadge({ status }) {
  const map = {
    pending:    { label: 'Pending',    cls: 'badge-pending'    },
    processing: { label: 'Processing', cls: 'badge-processing' },
    done:       { label: 'Done',       cls: 'badge-done'       },
    error:      { label: 'Error',      cls: 'badge-error'      },
  }
  const { label, cls } = map[status] || map.pending
  return (
    <span className={`badge ${cls}`}>
      <span className="badge-dot" />
      {label}
    </span>
  )
}

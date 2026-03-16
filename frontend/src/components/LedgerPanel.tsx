interface LedgerPanelProps {
  ledger: any
}

export default function LedgerPanel({ ledger }: LedgerPanelProps) {
  if (!ledger) {
    return (
      <div className="text-haf9-text-muted text-sm">
        원장을 로드하는 중...
      </div>
    )
  }

  const entries = ledger.entries || []

  if (entries.length === 0) {
    return (
      <div className="text-haf9-text-muted text-sm">
        기록된 이벤트가 없습니다.
      </div>
    )
  }

  const getEventColor = (eventType: string) => {
    if (eventType.includes('RECEIVED') || eventType.includes('PARSED')) return 'text-blue-400'
    if (eventType.includes('GENERATED') || eventType.includes('COMPILED')) return 'text-purple-400'
    if (eventType.includes('APPLIED')) return 'text-green-400'
    if (eventType.includes('DECISION')) return 'text-yellow-400'
    if (eventType.includes('REJECTED') || eventType.includes('ROLLBACK')) return 'text-red-400'
    return 'text-gray-400'
  }

  return (
    <div className="space-y-2 max-h-96 overflow-y-auto">
      {entries.map((entry: any, index: number) => (
        <div 
          key={entry.event_id || index} 
          className="bg-haf9-dark rounded p-2 text-xs border-l-2 border-haf9-border"
        >
          <div className="flex items-center justify-between mb-1">
            <span className={`font-medium ${getEventColor(entry.event_type)}`}>
              {entry.event_type}
            </span>
            <span className="text-haf9-text-muted">
              {new Date(entry.timestamp).toLocaleTimeString('ko-KR')}
            </span>
          </div>
          <div className="text-haf9-text-muted truncate">
            {entry.explanation}
          </div>
          {entry.related_entity_ids && entry.related_entity_ids.length > 0 && (
            <div className="text-haf9-text-muted mt-1">
              관련: {entry.related_entity_ids.join(', ').substring(0, 30)}...
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

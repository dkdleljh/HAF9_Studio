interface PatchListProps {
  candidates: any[]
  selectedId: string | null
  onSelect: (id: string) => void
}

export default function PatchList({ candidates, selectedId, onSelect }: PatchListProps) {
  if (!candidates || candidates.length === 0) {
    return (
      <div className="text-haf9-text-muted text-sm">
        생성된 패치가 없습니다.
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {candidates.map((patch) => (
        <div
          key={patch.patch_id}
          onClick={() => onSelect(patch.patch_id)}
          className={`p-3 rounded cursor-pointer border transition-all ${
            selectedId === patch.patch_id
              ? 'border-haf9-accent bg-haf9-accent/10'
              : 'border-haf9-border hover:border-haf9-accent/50'
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-sm text-haf9-accent">
              {patch.patch_type}
            </span>
            <PriorityBadge priority={patch.scoring_metadata?.priority} />
          </div>
          
          <div className="text-sm text-haf9-text mb-2">
            {patch.rationale}
          </div>
          
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="text-haf9-text-muted">
              대상: {patch.target_cells?.length || 0}개 셀
            </span>
            {patch.expected_effects && (
              <span className="text-green-400">
                효과: {Object.entries(patch.expected_effects).map(([k, v]) => 
                  `${k}: +${((v as number) * 100).toFixed(0)}%`
                ).join(', ')}
              </span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function PriorityBadge({ priority }: { priority?: number }) {
  if (!priority) return null
  
  let color = 'bg-gray-500'
  if (priority >= 0.8) color = 'bg-green-500'
  else if (priority >= 0.6) color = 'bg-yellow-500'
  else color = 'bg-red-500'

  return (
    <span className={`px-2 py-0.5 rounded text-xs text-white ${color}`}>
      우선순위: {(priority * 100).toFixed(0)}%
    </span>
  )
}

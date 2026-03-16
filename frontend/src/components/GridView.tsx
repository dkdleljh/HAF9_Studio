interface GridViewProps {
  state: any
}

export default function GridView({ state }: GridViewProps) {
  if (!state) {
    return (
      <div className="flex items-center justify-center h-64 text-haf9-text-muted">
        시나리오를 로드하는 중...
      </div>
    )
  }

  const { width, height, cells, zones, exits, obstacles } = state
  
  // 셀 타입별 색상
  const getCellColor = (x: number, y: number) => {
    const key = `${x},${y}`
    const cell = cells?.[key]
    
    // 장애물 확인
    const isObstacle = obstacles?.some((o: any) => o.location[0] === x && o.location[1] === y)
    if (isObstacle) return 'bg-red-800'
    
    // 출구 확인
    const isExit = exits?.some((e: any) => e.location[0] === x && e.location[1] === y)
    if (isExit) return 'bg-green-500'
    
    // 존 확인
    for (const [zoneId, zone] of Object.entries(zones || {})) {
      if ((zone as any).cells?.some((c: any) => c[0] === x && c[1] === y)) {
        if (zoneId === 'zone1') return 'bg-blue-900/50'
        if (zoneId === 'zone2') return 'bg-purple-900/50'
        if (zoneId === 'zone3') return 'bg-orange-900/50'
      }
    }
    
    // 기본 셀
    const occupancy = cell?.occupancy_flow || 0
    if (occupancy > 0.7) return 'bg-yellow-600'
    if (occupancy > 0.4) return 'bg-yellow-800'
    
    return 'bg-haf9-dark'
  }

  return (
    <div className="overflow-auto">
      <div 
        className="grid gap-0.5 mx-auto"
        style={{ 
          gridTemplateColumns: `repeat(${width}, minmax(20px, 1fr))`,
          maxWidth: `${width * 24}px`
        }}
      >
        {Array.from({ length: height }).map((_, y) =>
          Array.from({ length: width }).map((_, x) => (
            <div
              key={`${x}-${y}`}
              className={`w-full aspect-square ${getCellColor(x, y)} rounded-sm grid-cell`}
              title={`Cell (${x}, ${y})`}
            />
          ))
        )}
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-900/50 rounded-sm"></div>
          <span>Zone 1 (Operations)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-purple-900/50 rounded-sm"></div>
          <span>Zone 2 (Assembly)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-900/50 rounded-sm"></div>
          <span>Zone 3 (Laboratory)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded-sm"></div>
          <span>출구 (Exit)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-800 rounded-sm"></div>
          <span>장애물 (Obstacle)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-600 rounded-sm"></div>
          <span>혼잡 (Congested)</span>
        </div>
      </div>

      {/* Zone Info */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        {Object.entries(zones || {}).map(([id, zone]: [string, any]) => (
          <div key={id} className="bg-haf9-dark rounded p-3 text-sm">
            <div className="font-semibold text-haf9-accent">{zone.name}</div>
            <div className="text-haf9-text-muted mt-1">
              <div>대피 시간: {zone.evacuation_time_estimate?.toFixed(1)}s</div>
              <div>인구 밀도: {(zone.crowd_density * 100).toFixed(0)}%</div>
              <div>접근성: {(zone.accessibility * 100).toFixed(0)}%</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

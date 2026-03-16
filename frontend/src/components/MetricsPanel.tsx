interface MetricsPanelProps {
  metrics: any
}

export default function MetricsPanel({ metrics }: MetricsPanelProps) {
  if (!metrics) {
    return (
      <div className="text-haf9-text-muted text-sm">
        메트릭을 로드하는 중...
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {Object.entries(metrics).map(([zoneId, zoneMetrics]: [string, any]) => (
        <div key={zoneId} className="bg-haf9-dark rounded p-3">
          <div className="font-semibold text-haf9-accent mb-2">{zoneId.toUpperCase()}</div>
          
          <div className="space-y-2">
            <MetricBar 
              label="대피 시간" 
              value={zoneMetrics.evacuation_time_estimate} 
              unit="s"
              max={20}
              target={12}
              format={(v) => v?.toFixed(1) || '0'}
            />
            <MetricBar 
              label="인구 밀도" 
              value={zoneMetrics.crowd_density} 
              unit="%"
              max={1}
              format={(v) => ((v || 0) * 100).toFixed(0)}
            />
            <MetricBar 
              label="피크 스트레스" 
              value={zoneMetrics.peak_stress} 
              unit=""
              max={1}
              format={(v) => ((v || 0) * 100).toFixed(0)}
              inverse
            />
            <MetricBar 
              label="접근성" 
              value={zoneMetrics.accessibility} 
              unit="%"
              max={1}
              format={(v) => ((v || 0) * 100).toFixed(0)}
            />
            <MetricBar 
              label="소음" 
              value={zoneMetrics.noise_level} 
              unit="dB"
              max={100}
              format={(v) => v?.toFixed(0) || '0'}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

function MetricBar({ 
  label, 
  value, 
  unit, 
  max, 
  target,
  format, 
  inverse = false 
}: { 
  label: string
  value?: number
  unit: string
  max: number
  target?: number
  format: (v: number) => string
  inverse?: boolean
}) {
  const percentage = value ? Math.min((value / max) * 100, 100) : 0
  
  let barColor = 'bg-haf9-accent'
  if (target !== undefined) {
    if (inverse) {
      barColor = value <= target ? 'bg-green-500' : 'bg-red-500'
    } else {
      barColor = value <= target ? 'bg-green-500' : 'bg-yellow-500'
    }
  }

  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-haf9-text-muted">{label}</span>
        <span className="text-haf9-text">
          {format(value)} {unit}
          {target && (
            <span className="text-haf9-text-muted ml-1">
              (목표: {target}{unit})
            </span>
          )}
        </span>
      </div>
      <div className="h-1.5 bg-haf9-border rounded overflow-hidden">
        <div 
          className={`h-full ${barColor} transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

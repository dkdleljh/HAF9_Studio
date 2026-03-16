interface IntentPanelProps {
  onSubmit: (text: string) => void
  isLoading: boolean
}

export default function IntentPanel({ onSubmit, isLoading }: IntentPanelProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const input = form.elements.namedItem('intent') as HTMLInputElement
    if (input.value.trim()) {
      onSubmit(input.value.trim())
      input.value = ''
    }
  }

  const exampleIntents = [
    "Reduce evacuation time in zone3 to under 12 seconds while maintaining structural safety",
    "Improve accessibility in zone1",
    "Optimize flow between zone2 and exit",
  ]

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          name="intent"
          type="text"
          placeholder="인텐트를 입력하세요 (예: zone3의 대피 시간을 12초 이하로 줄이기)"
          className="flex-1 bg-haf9-dark border border-haf9-border rounded px-4 py-2 text-haf9-text placeholder-haf9-text-muted focus:outline-none focus:border-haf9-accent"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-6 py-2 bg-haf9-accent hover:bg-haf9-accent-hover disabled:opacity-50 rounded font-medium transition-colors"
        >
          {isLoading ? '처리중...' : '분석'}
        </button>
      </form>

      <div className="mt-3 text-sm text-haf9-text-muted">
        <span>예시: </span>
        {exampleIntents.map((intent, i) => (
          <button
            key={i}
            onClick={() => onSubmit(intent)}
            className="text-haf9-accent hover:underline ml-1"
            disabled={isLoading}
          >
            {i + 1}.
          </button>
        ))}
      </div>
    </div>
  )
}

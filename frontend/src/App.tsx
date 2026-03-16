import { useState, useEffect } from 'react'
import GridView from './components/GridView'
import IntentPanel from './components/IntentPanel'
import MetricsPanel from './components/MetricsPanel'
import PatchList from './components/PatchList'
import LedgerPanel from './components/LedgerPanel'
import { api } from './services/api'

function App() {
  const [gridState, setGridState] = useState<any>(null)
  const [metrics, setMetrics] = useState<any>(null)
  const [currentStep, setCurrentStep] = useState<string>('idle')
  const [parsedIntent, setParsedIntent] = useState<any>(null)
  const [dslData, setDslData] = useState<any>(null)
  const [irData, setIrData] = useState<any>(null)
  const [candidates, setCandidates] = useState<any[]>([])
  const [selectedPatch, setSelectedPatch] = useState<any>(null)
  const [safetyResult, setSafetyResult] = useState<any>(null)
  const [ledger, setLedger] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  // 시나리오 로드
  useEffect(() => {
    loadExampleScenario()
  }, [])

  const loadExampleScenario = async () => {
    try {
      setCurrentStep('loading')
      const response = await api.loadExample()
      setGridState(response.snapshot)
      setMetrics(response.metrics)
      setCurrentStep('ready')
    } catch (err: any) {
      setError(`시나리오 로드 실패: ${err.message}`)
      setCurrentStep('error')
    }
  }

  const handleIntentSubmit = async (text: string) => {
    try {
      setCurrentStep('parsing')
      setError(null)
      
      // 1. 인텐트 파싱
      const parsed = await api.parseIntent(text)
      setParsedIntent(parsed)
      
      if (parsed.requires_human_review) {
        setCurrentStep('review_needed')
        return
      }

      // 2. DSL 생성
      setCurrentStep('compiling_dsl')
      const dsl = await api.compileDsl({
        ...parsed,
        raw_text: text
      })
      setDslData(dsl)

      // 3. IR 컴파일
      setCurrentStep('compiling_ir')
      const ir = await api.compileIr(dsl)
      setIrData(ir)

      // 4. 패치 생성
      setCurrentStep('generating_patches')
      const patches = await api.generatePatches(ir)
      setCandidates(patches.candidates)
      setCurrentStep('patches_ready')

    } catch (err: any) {
      setError(`인텐트 처리 실패: ${err.message}`)
      setCurrentStep('error')
    }
  }

  const handlePatchSelect = async (patchId: string) => {
    try {
      setSelectedPatch(patchId)
      setCurrentStep('verifying')
      
      const result = await api.verifyPatch(patchId)
      setSafetyResult(result)
      
      if (result.decision === 'APPROVED') {
        setCurrentStep('approved')
      } else if (result.decision === 'REQUIRES_HUMAN_REVIEW') {
        setCurrentStep('review_needed')
      } else {
        setCurrentStep('rejected')
      }
    } catch (err: any) {
      setError(`패치 검증 실패: ${err.message}`)
    }
  }

  const handleApplyPatch = async () => {
    if (!selectedPatch) return

    try {
      setCurrentStep('applying')
      const result = await api.applyPatch(selectedPatch)
      
      setGridState(result.diff)
      setMetrics(result.metrics_after)
      
      // 원장 새로고침
      const ledgerData = await api.getLedger()
      setLedger(ledgerData)
      
      setCurrentStep('applied')
    } catch (err: any) {
      setError(`패치 적용 실패: ${err.message}`)
    }
  }

  const loadLedger = async () => {
    try {
      const data = await api.getLedger()
      setLedger(data)
    } catch (err: any) {
      console.error('원장 로드 실패:', err)
    }
  }

  return (
    <div className="min-h-screen bg-haf9-dark">
      {/* Header */}
      <header className="bg-haf9-card border-b border-haf9-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-haf9-accent font-mono">
              HAF-9_Studio
            </h1>
            <span className="text-haf9-text-muted text-sm">
              공간 운영 체제 | Spatial Operating System
            </span>
          </div>
          <div className="flex items-center gap-4">
            <StatusBadge step={currentStep} />
            <button 
              onClick={loadExampleScenario}
              className="px-4 py-2 bg-haf9-card border border-haf9-border rounded hover:bg-haf9-border transition-colors text-sm"
            >
              시나리오Reload
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6 grid grid-cols-12 gap-6">
        {/* Left Panel - Grid & Intent */}
        <div className="col-span-8 space-y-6">
          {/* Grid View */}
          <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
              공간 디지털 트윈
            </h2>
            <GridView state={gridState} />
          </div>

          {/* Intent Input */}
          <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              인텐트 입력
            </h2>
            <IntentPanel onSubmit={handleIntentSubmit} isLoading={currentStep === 'parsing'} />
          </div>

          {/* Parsed Intent Display */}
          {parsedIntent && (
            <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                파싱된 인텐트
              </h2>
              <IntentDisplay intent={parsedIntent} dsl={dslData} ir={irData} />
            </div>
          )}

          {/* Patch Candidates */}
          {candidates.length > 0 && (
            <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                패치 후보
              </h2>
              <PatchList 
                candidates={candidates} 
                selectedId={selectedPatch}
                onSelect={handlePatchSelect}
              />
              {safetyResult && (
                <SafetyResult 
                  result={safetyResult} 
                  onApply={handleApplyPatch}
                  canApply={safetyResult.decision === 'APPROVED'}
                />
              )}
            </div>
          )}
        </div>

        {/* Right Panel - Metrics & Ledger */}
        <div className="col-span-4 space-y-6">
          {/* Metrics */}
          <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              메트릭
            </h2>
            <MetricsPanel metrics={metrics} />
          </div>

          {/* Ledger */}
          <div className="bg-haf9-card border border-haf9-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <svg className="w-5 h-5 text-haf9-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                포렌식 원장
              </h2>
              <button 
                onClick={loadLedger}
                className="text-sm text-haf9-accent hover:underline"
              >
                새로고침
              </button>
            </div>
            <LedgerPanel ledger={ledger} />
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
              <h3 className="text-red-400 font-semibold mb-2">오류</h3>
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function StatusBadge({ step }: { step: string }) {
  const statusMap: Record<string, { label: string; color: string }> = {
    idle: { label: '대기중', color: 'bg-gray-500' },
    loading: { label: '로딩중', color: 'bg-yellow-500' },
    ready: { label: '준비됨', color: 'bg-green-500' },
    parsing: { label: '파싱중', color: 'bg-blue-500' },
    compiling_dsl: { label: 'DSL 컴파일', color: 'bg-blue-500' },
    compiling_ir: { label: 'IR 컴파일', color: 'bg-blue-500' },
    generating_patches: { label: '패치 생성', color: 'bg-purple-500' },
    patches_ready: { label: '패치 준비됨', color: 'bg-green-500' },
    verifying: { label: '검증중', color: 'bg-orange-500' },
    approved: { label: '승인됨', color: 'bg-green-500' },
    rejected: { label: '거부됨', color: 'bg-red-500' },
    review_needed: { label: '검토 필요', color: 'bg-yellow-500' },
    applying: { label: '적용중', color: 'bg-blue-500' },
    applied: { label: '적용됨', color: 'bg-green-500' },
    error: { label: '오류', color: 'bg-red-500' },
  }

  const status = statusMap[step] || { label: step, color: 'bg-gray-500' }

  return (
    <div className={`px-3 py-1 rounded-full text-xs font-medium text-white ${status.color}`}>
      {status.label}
    </div>
  )
}

function IntentDisplay({ intent, dsl, ir }: { intent: any; dsl?: any; ir?: any }) {
  return (
    <div className="space-y-4">
      <div className="bg-haf9-dark rounded p-3 font-mono text-sm">
        <div className="text-haf9-text-muted mb-2">인텐트 ID:</div>
        <div className="text-haf9-accent">{intent.intent_id}</div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-haf9-text-muted text-sm mb-1">유형:</div>
          <div className="text-haf9-text">{intent.intent_type}</div>
        </div>
        <div>
          <div className="text-haf9-text-muted text-sm mb-1">대상 존:</div>
          <div className="text-haf9-text">{intent.target_zone || '없음'}</div>
        </div>
        <div>
          <div className="text-haf9-text-muted text-sm mb-1">목적:</div>
          <div className="text-haf9-text">{intent.objective}</div>
        </div>
        <div>
          <div className="text-haf9-text-muted text-sm mb-1">모호성:</div>
          <div className="text-haf9-text">{intent.ambiguity_level} ({intent.ambiguity_score})</div>
        </div>
      </div>

      {intent.warnings && intent.warnings.length > 0 && (
        <div className="bg-yellow-900/20 border border-yellow-500 rounded p-3">
          <div className="text-yellow-400 text-sm font-semibold mb-2">경고</div>
          {intent.warnings.map((w: any, i: number) => (
            <div key={i} className="text-yellow-300 text-sm">• {w.message}</div>
          ))}
        </div>
      )}

      {dsl && (
        <div className="bg-haf9-dark rounded p-3">
          <div className="text-haf9-text-muted text-sm mb-2">DSL:</div>
          <pre className="text-xs text-haf9-text overflow-x-auto">
            {JSON.stringify(dsl, null, 2)}
          </pre>
        </div>
      )}

      {ir && (
        <div className="bg-haf9-dark rounded p-3">
          <div className="text-haf9-text-muted text-sm mb-2">IR:</div>
          <pre className="text-xs text-haf9-text overflow-x-auto">
            {JSON.stringify(ir, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

function SafetyResult({ result, onApply, canApply }: { result: any; onApply: () => void; canApply: boolean }) {
  return (
    <div className={`mt-4 rounded-lg p-4 border ${
      result.decision === 'APPROVED' 
        ? 'bg-green-900/20 border-green-500' 
        : result.decision === 'REQUIRES_HUMAN_REVIEW'
        ? 'bg-yellow-900/20 border-yellow-500'
        : 'bg-red-900/20 border-red-500'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className={`font-semibold ${
          result.decision === 'APPROVED' 
            ? 'text-green-400' 
            : result.decision === 'REQUIRES_HUMAN_REVIEW'
            ? 'text-yellow-400'
            : 'text-red-400'
        }`}>
          안전성 검증 결과: {result.decision}
        </h3>
        {canApply && (
          <button
            onClick={onApply}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded text-white text-sm font-medium transition-colors"
          >
            패치 적용
          </button>
        )}
      </div>
      
      {result.violations && result.violations.length > 0 && (
        <div className="mb-3">
          <div className="text-red-400 text-sm font-semibold mb-1">위반 사항:</div>
          {result.violations.map((v: any, i: number) => (
            <div key={i} className="text-red-300 text-sm">• {v.message}</div>
          ))}
        </div>
      )}

      {result.warnings && result.warnings.length > 0 && (
        <div>
          <div className="text-yellow-400 text-sm font-semibold mb-1">경고:</div>
          {result.warnings.map((w: any, i: number) => (
            <div key={i} className="text-yellow-300 text-sm">• {w.message}</div>
          ))}
        </div>
      )}

      <div className="mt-3 text-haf9-text-muted text-sm">
        {result.explanation}
      </div>
    </div>
  )
}

export default App

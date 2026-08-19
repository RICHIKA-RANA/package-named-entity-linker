import { useEffect, useState, Suspense } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Group, Panel, Separator, type Layout } from 'react-resizable-panels'
import { motion } from 'motion/react'
import { X, SplitSquareHorizontal } from 'lucide-react'
import { getNamespace, type Namespace } from '../api'
import { NamespaceProvider } from './namespaceContext'
import {
  PANE_VIEWS,
  getPaneView,
  isViewKey,
  otherDefaultView,
  DEFAULT_LEFT_VIEW,
  type ViewKey,
} from './paneViews'
import { useMediaQuery } from '../hooks/useMediaQuery'

interface PaneState {
  left: ViewKey
  right: ViewKey | null
}

interface StoredWorkspaceState extends PaneState {
  layout?: Layout
}

function loadStoredState(namespace: string): StoredWorkspaceState | null {
  try {
    const raw = localStorage.getItem(`pane-state:${namespace}`)
    if (!raw) return null

    const parsed = JSON.parse(raw)
    if (!isViewKey(parsed.left)) return null
    if (parsed.right !== null && !isViewKey(parsed.right)) return null

    return { left: parsed.left, right: parsed.right, layout: parsed.layout }
  } catch {
    return null
  }
}

function NamespaceWorkspaceInner({ name }: { name: string }) {
  const [namespace, setNamespace] = useState<Namespace | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchParams, setSearchParams] = useSearchParams()
  const isWideEnough = useMediaQuery('(min-width: 900px)')

  const [storedLayout, setStoredLayout] = useState<Layout | undefined>(
    () => loadStoredState(name)?.layout,
  )

  const [paneState, setPaneState] = useState<PaneState>(() => {
    const left = searchParams.get('left')
    const right = searchParams.get('right')
    const stored = loadStoredState(name)

    if (isViewKey(left)) {
      return { left, right: isViewKey(right) ? right : null }
    }

    if (stored) return { left: stored.left, right: stored.right }

    return { left: DEFAULT_LEFT_VIEW, right: null }
  })

  useEffect(() => {
    getNamespace(name)
      .then(setNamespace)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load namespace')
      })
      .finally(() => setLoading(false))
  }, [name])

  useEffect(() => {
    const stored: StoredWorkspaceState = { ...paneState, layout: storedLayout }
    localStorage.setItem(`pane-state:${name}`, JSON.stringify(stored))

    const params: Record<string, string> = { left: paneState.left }
    if (paneState.right) params.right = paneState.right
    setSearchParams(params, { replace: true })
  }, [paneState, storedLayout, name, setSearchParams])

  function handleLayoutChanged(layout: Layout) {
    setStoredLayout(layout)
  }

  function handleSplit() {
    setPaneState((current) => ({
      ...current,
      right: current.right ?? otherDefaultView(current.left),
    }))
  }

  function handleCloseSplit() {
    setPaneState((current) => ({ left: current.left, right: null }))
  }

  function handleSelectView(pane: 'left' | 'right', view: ViewKey) {
    setPaneState((current) => ({ ...current, [pane]: view }))
  }

  const orientation = isWideEnough ? 'horizontal' : 'vertical'

  return (
    <section className="workspace">
      <p>
        <Link to="/">&larr; Back to namespaces</Link>
      </p>

      {loading && <p>Loading&hellip;</p>}
      {error && <p className="error">{error}</p>}

      {namespace && (
        <>
          <div className="workspace-header">
            <h2>{namespace.name}</h2>
            {namespace.description && <p className="muted">{namespace.description}</p>}
          </div>

          <Group
            key={paneState.right ? 'split' : 'single'}
            orientation={orientation}
            className={`pane-group pane-group-${orientation}`}
            defaultLayout={storedLayout}
            onLayoutChanged={handleLayoutChanged}
          >
            <Panel id="left" minSize="20" className="pane">
              <PaneHeader
                current={paneState.left}
                onSelect={(view) => handleSelectView('left', view)}
                onSplit={paneState.right ? undefined : handleSplit}
              />
              <PaneContent namespace={name} view={paneState.left} />
            </Panel>

            {paneState.right && (
              <>
                <Separator className="resize-handle" />
                <Panel id="right" minSize="20" className="pane">
                  <PaneHeader
                    current={paneState.right}
                    onSelect={(view) => handleSelectView('right', view)}
                    onClose={handleCloseSplit}
                  />
                  <PaneContent namespace={name} view={paneState.right} />
                </Panel>
              </>
            )}
          </Group>
        </>
      )}
    </section>
  )
}

function PaneHeader({
  current,
  onSelect,
  onSplit,
  onClose,
}: {
  current: ViewKey
  onSelect: (view: ViewKey) => void
  onSplit?: () => void
  onClose?: () => void
}) {
  return (
    <div className="pane-header">
      <div className="pane-tabs">
        {PANE_VIEWS.map((view) => (
          <button
            key={view.key}
            type="button"
            className={view.key === current ? 'pane-tab active' : 'pane-tab'}
            onClick={() => onSelect(view.key)}
          >
            <view.icon size={14} />
            {view.label}
          </button>
        ))}
      </div>
      <div className="pane-actions">
        {onSplit && (
          <button
            type="button"
            className="icon-button"
            onClick={onSplit}
            aria-label="Split view"
            title="Split view"
          >
            <SplitSquareHorizontal size={16} />
          </button>
        )}
        {onClose && (
          <button
            type="button"
            className="icon-button"
            onClick={onClose}
            aria-label="Close split"
            title="Close split"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  )
}

function PaneContent({ namespace, view }: { namespace: string; view: ViewKey }) {
  const { Component } = getPaneView(view)

  return (
    <div className="pane-body">
      <NamespaceProvider value={{ namespace }}>
        <Suspense fallback={<p>Loading&hellip;</p>}>
          <motion.div
            key={view}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.12 }}
          >
            <Component />
          </motion.div>
        </Suspense>
      </NamespaceProvider>
    </div>
  )
}

export default function NamespaceWorkspace() {
  const { name } = useParams<{ name: string }>()

  if (!name) return null

  return <NamespaceWorkspaceInner key={name} name={name} />
}

import { lazy, type ComponentType } from 'react'
import { Sparkles, FlaskConical, GitCommitHorizontal, Search, Code2 } from 'lucide-react'
import NamespaceTrain from './NamespaceTrain'
import NamespaceTests from './NamespaceTests'
import NamespaceHistory from './NamespaceHistory'
import NamespaceCode from './NamespaceCode'

const NamespaceInspect = lazy(() => import('./NamespaceInspect'))

export type ViewKey = 'train' | 'test' | 'history' | 'inspect' | 'code'

export const VIEW_KEYS: ViewKey[] = ['train', 'test', 'history', 'inspect', 'code']

export const DEFAULT_LEFT_VIEW: ViewKey = 'train'
export const DEFAULT_RIGHT_VIEW: ViewKey = 'test'

interface PaneView {
  key: ViewKey
  label: string
  icon: ComponentType<{ size?: number }>
  Component: ComponentType
}

export const PANE_VIEWS: PaneView[] = [
  { key: 'train', label: 'Train', icon: Sparkles, Component: NamespaceTrain },
  { key: 'test', label: 'Tests', icon: FlaskConical, Component: NamespaceTests },
  { key: 'history', label: 'History', icon: GitCommitHorizontal, Component: NamespaceHistory },
  { key: 'inspect', label: 'Inspect', icon: Search, Component: NamespaceInspect },
  { key: 'code', label: 'Code', icon: Code2, Component: NamespaceCode },
]

// Old bookmarks/localStorage entries and shared links may still reference
// the pre-merge "graph" view key - route them to the merged Inspect tab.
const LEGACY_VIEW_ALIASES: Record<string, ViewKey> = { graph: 'inspect' }

export function isViewKey(value: string | null | undefined): value is ViewKey {
  return VIEW_KEYS.includes(value as ViewKey)
}

export function normalizeViewKey(value: string | null | undefined): ViewKey | null {
  if (isViewKey(value)) return value
  if (value && value in LEGACY_VIEW_ALIASES) return LEGACY_VIEW_ALIASES[value]
  return null
}

export function getPaneView(key: ViewKey): PaneView {
  const view = PANE_VIEWS.find((candidate) => candidate.key === key)

  if (!view) {
    throw new Error(`Unknown pane view: ${key}`)
  }

  return view
}

export function otherDefaultView(view: ViewKey): ViewKey {
  return view === DEFAULT_LEFT_VIEW ? DEFAULT_RIGHT_VIEW : DEFAULT_LEFT_VIEW
}

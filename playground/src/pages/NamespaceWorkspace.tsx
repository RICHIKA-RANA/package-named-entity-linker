import { useEffect, useState, Suspense, type FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Group, Panel, Separator, type Layout } from 'react-resizable-panels'
import { motion } from 'motion/react'
import { X, SplitSquareHorizontal, GitCommitHorizontal, Pencil, Trash2 } from 'lucide-react'
import {
  ApiError,
  commitNamespace,
  deleteNamespace,
  getNamespace,
  updateNamespace,
  type Namespace,
} from '../api'
import { NamespaceProvider } from './namespaceContext'
import { useToast } from '../components/toastContext'
import Modal from '../components/Modal'
import ActionMenu from '../components/ActionMenu'
import {
  PANE_VIEWS,
  getPaneView,
  normalizeViewKey,
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
    const left = normalizeViewKey(parsed.left)
    if (!left) return null

    return { left, right: normalizeViewKey(parsed.right), layout: parsed.layout }
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
  const navigate = useNavigate()
  const { showToast } = useToast()

  const [storedLayout, setStoredLayout] = useState<Layout | undefined>(
    () => loadStoredState(name)?.layout,
  )
  const [commitOpen, setCommitOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)

  // Bootstrap the URL from persisted layout the first time this namespace is
  // opened with no view params at all (e.g. a bare namespace link). Once the
  // URL carries a `left` param, every render derives view state from it
  // directly - single source of truth, so sidebar links, cross-pane links,
  // and browser back/forward all just work.
  useEffect(() => {
    if (normalizeViewKey(searchParams.get('left'))) return

    const stored = loadStoredState(name)
    const params: Record<string, string> = { left: stored?.left ?? DEFAULT_LEFT_VIEW }
    if (stored?.right) params.right = stored.right
    setSearchParams(params, { replace: true })
    // Bootstrap only - runs again if the namespace itself changes (new key from parent).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name])

  const left = normalizeViewKey(searchParams.get('left')) ?? DEFAULT_LEFT_VIEW
  const right = normalizeViewKey(searchParams.get('right'))

  useEffect(() => {
    getNamespace(name)
      .then(setNamespace)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load namespace')
      })
      .finally(() => setLoading(false))
  }, [name])

  useEffect(() => {
    const stored: StoredWorkspaceState = { left, right, layout: storedLayout }
    localStorage.setItem(`pane-state:${name}`, JSON.stringify(stored))
  }, [left, right, storedLayout, name])

  function handleLayoutChanged(layout: Layout) {
    setStoredLayout(layout)
  }

  function updateViews(next: { left?: ViewKey; right?: ViewKey | null }) {
    setSearchParams((current) => {
      const params = new URLSearchParams(current)
      if (next.left) params.set('left', next.left)
      if (next.right === null) params.delete('right')
      else if (next.right) params.set('right', next.right)
      return params
    })
  }

  function handleSplit() {
    if (right) return
    updateViews({ right: otherDefaultView(left) })
  }

  function handleCloseSplit() {
    updateViews({ right: null })
  }

  function handleSelectView(pane: 'left' | 'right', view: ViewKey) {
    updateViews(pane === 'left' ? { left: view } : { right: view })
  }

  async function handleCommit(message: string) {
    await commitNamespace(name, message)
    showToast('Committed current state')
    setCommitOpen(false)
  }

  async function handleUpdateDescription(description: string | null) {
    const updated = await updateNamespace(name, description)
    setNamespace(updated)
    showToast('Namespace updated')
    setEditOpen(false)
  }

  async function handleDeleteNamespace() {
    await deleteNamespace(name)
    showToast('Namespace deleted')
    navigate('/')
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
            <div>
              <h2>{namespace.name}</h2>
              {namespace.description && <p className="muted">{namespace.description}</p>}
            </div>
            <div className="workspace-actions">
              <button type="button" onClick={() => setCommitOpen(true)}>
                <GitCommitHorizontal size={14} />
                Commit
              </button>
              {!right && (
                <button type="button" className="secondary" onClick={handleSplit}>
                  <SplitSquareHorizontal size={14} />
                  Split view
                </button>
              )}
              <ActionMenu
                items={[
                  { label: 'Edit description', icon: Pencil, onClick: () => setEditOpen(true) },
                  {
                    label: 'Delete namespace',
                    icon: Trash2,
                    destructive: true,
                    onClick: () => setDeleteOpen(true),
                  },
                ]}
              />
            </div>
          </div>

          <Group
            key={right ? 'split' : 'single'}
            orientation={orientation}
            className={`pane-group pane-group-${orientation}`}
            defaultLayout={storedLayout}
            onLayoutChanged={handleLayoutChanged}
          >
            <Panel id="left" minSize="20" className="pane">
              <PaneHeader current={left} />
              <PaneContent namespace={name} view={left} />
            </Panel>

            {right && (
              <>
                <Separator className="resize-handle" />
                <Panel id="right" minSize="20" className="pane">
                  <PaneHeader
                    current={right}
                    onSelect={(view) => handleSelectView('right', view)}
                    onClose={handleCloseSplit}
                  />
                  <PaneContent namespace={name} view={right} />
                </Panel>
              </>
            )}
          </Group>
        </>
      )}

      <CommitModal open={commitOpen} onOpenChange={setCommitOpen} onCommit={handleCommit} />

      <EditDescriptionModal
        open={editOpen}
        initialDescription={namespace?.description ?? ''}
        onOpenChange={setEditOpen}
        onSave={handleUpdateDescription}
      />

      <Modal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`Delete ${name}`}
        description="This permanently deletes every entity, fact, regex rule, and commit in this namespace. This cannot be undone."
      >
        <DeleteConfirmForm name={name} onDelete={handleDeleteNamespace} />
      </Modal>
    </section>
  )
}

function PaneHeader({
  current,
  onSelect,
  onClose,
}: {
  current: ViewKey
  onSelect?: (view: ViewKey) => void
  onClose?: () => void
}) {
  const view = getPaneView(current)

  return (
    <div className="pane-header">
      {onSelect ? (
        <div className="pane-tabs">
          {PANE_VIEWS.map((candidate) => (
            <button
              key={candidate.key}
              type="button"
              className={candidate.key === current ? 'pane-tab active' : 'pane-tab'}
              onClick={() => onSelect(candidate.key)}
            >
              <candidate.icon size={14} />
              {candidate.label}
            </button>
          ))}
        </div>
      ) : (
        <div className="pane-static-label">
          <view.icon size={14} />
          {view.label}
        </div>
      )}
      <div className="pane-actions">
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

function CommitModal({
  open,
  onOpenChange,
  onCommit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCommit: (message: string) => Promise<void>
}) {
  const [message, setMessage] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!message.trim()) {
      setFormError('Enter a commit message')
      return
    }

    setSubmitting(true)

    try {
      await onCommit(message.trim())
      setMessage('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to commit')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Commit current state">
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="workspace-commit-message">Message</label>
          <input
            id="workspace-commit-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add mayank entity and greeting facts"
            autoFocus
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Committing…' : 'Commit current state'}
        </button>
      </form>
    </Modal>
  )
}

function EditDescriptionModal({
  open,
  initialDescription,
  onOpenChange,
  onSave,
}: {
  open: boolean
  initialDescription: string
  onOpenChange: (open: boolean) => void
  onSave: (description: string | null) => Promise<void>
}) {
  const [description, setDescription] = useState(initialDescription)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    try {
      await onSave(description.trim() || null)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update namespace')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="Edit description">
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="workspace-edit-description">Description</label>
          <input
            id="workspace-edit-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            autoFocus
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Save'}
        </button>
      </form>
    </Modal>
  )
}

function DeleteConfirmForm({ name, onDelete }: { name: string; onDelete: () => Promise<void> }) {
  const [confirmText, setConfirmText] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()

    if (confirmText !== name) {
      setFormError('Type the namespace name exactly to confirm')
      return
    }

    setDeleting(true)
    setFormError(null)

    try {
      await onDelete()
    } catch (err) {
      setFormError(
        err instanceof ApiError ? err.message : 'Failed to delete namespace',
      )
      setDeleting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="workspace-confirm-delete-name">
          Type <strong>{name}</strong> to confirm
        </label>
        <input
          id="workspace-confirm-delete-name"
          value={confirmText}
          onChange={(e) => setConfirmText(e.target.value)}
          autoFocus
        />
      </div>
      {formError && <p className="error">{formError}</p>}
      <button type="submit" className="destructive" disabled={deleting}>
        {deleting ? 'Deleting…' : 'Delete namespace'}
      </button>
    </form>
  )
}

export default function NamespaceWorkspace() {
  const { name } = useParams<{ name: string }>()

  if (!name) return null

  return <NamespaceWorkspaceInner key={name} name={name} />
}

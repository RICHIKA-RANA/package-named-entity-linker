import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'motion/react'
import { Plus, Database, Tag, Share2, GitCommitHorizontal, Trash2, Pencil } from 'lucide-react'
import {
  ApiError,
  createNamespace,
  deleteNamespace,
  listCommits,
  listEntities,
  listFacts,
  listNamespaces,
  updateNamespace,
  type Namespace,
} from '../api'
import { bucketByDay } from '../charts/activity'
import ActivityChart from '../charts/ActivityChart'
import BarChart from '../charts/BarChart'
import Modal from '../components/Modal'
import ActionMenu from '../components/ActionMenu'
import { useToast } from '../components/toastContext'

interface NamespaceStats {
  namespace: Namespace
  entityCount: number
  factCount: number
  commitTimestamps: string[]
}

async function loadStats(namespace: Namespace): Promise<NamespaceStats> {
  const [entities, facts, commits] = await Promise.all([
    listEntities(namespace.name).catch(() => []),
    listFacts(namespace.name).catch(() => []),
    listCommits(namespace.name).catch(() => []),
  ])

  return {
    namespace,
    entityCount: entities.length,
    factCount: facts.length,
    commitTimestamps: commits.map((commit) => commit.created_at),
  }
}

export default function Dashboard() {
  const [stats, setStats] = useState<NamespaceStats[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<Namespace | null>(null)
  const [deleting, setDeleting] = useState<Namespace | null>(null)
  const { showToast } = useToast()

  useEffect(() => {
    refresh()
  }, [])

  async function refresh() {
    setLoading(true)
    setLoadError(null)

    try {
      const namespaces = await listNamespaces()
      const results = await Promise.all(namespaces.map(loadStats))
      setStats(results)
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load namespaces')
    } finally {
      setLoading(false)
    }
  }

  const totalEntities = stats.reduce((sum, s) => sum + s.entityCount, 0)
  const totalFacts = stats.reduce((sum, s) => sum + s.factCount, 0)
  const totalCommits = stats.reduce((sum, s) => sum + s.commitTimestamps.length, 0)

  const entityChartData = stats
    .slice()
    .sort((a, b) => b.entityCount - a.entityCount)
    .slice(0, 8)
    .map((s) => ({ label: s.namespace.name, value: s.entityCount }))

  const activityData = bucketByDay(
    stats.flatMap((s) => s.commitTimestamps),
    14,
    new Date(),
  )

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <button type="button" className="primary" onClick={() => setCreateOpen(true)}>
          <Plus size={16} />
          New namespace
        </button>
      </div>

      {loading && <p>Loading&hellip;</p>}
      {loadError && <p className="error">{loadError}</p>}

      {!loading && !loadError && (
        <>
          <div className="kpi-grid">
            <KpiCard icon={Database} label="Namespaces" value={stats.length} />
            <KpiCard icon={Tag} label="Entities" value={totalEntities} />
            <KpiCard icon={Share2} label="Facts" value={totalFacts} />
            <KpiCard icon={GitCommitHorizontal} label="Commits" value={totalCommits} />
          </div>

          <div className="chart-grid">
            <section className="card">
              <h3>Entities per namespace</h3>
              <BarChart data={entityChartData} ariaLabel="Entities per namespace" />
              {stats.length > entityChartData.length && (
                <p className="muted small">
                  +{stats.length - entityChartData.length} more namespace
                  {stats.length - entityChartData.length === 1 ? '' : 's'} not shown - see the list
                  below.
                </p>
              )}
            </section>
            <section className="card">
              <h3>Commit activity (last 14 days)</h3>
              <ActivityChart data={activityData} ariaLabel="Commit activity over the last 14 days" />
            </section>
          </div>

          <h3>Namespaces</h3>

          {stats.length === 0 && (
            <p className="muted">No namespaces yet - create one above to get started.</p>
          )}

          <div className="namespace-grid">
            {stats.map((s, index) => (
              <motion.div
                key={s.namespace.name}
                className="card namespace-card"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: Math.min(index * 0.03, 0.3) }}
              >
                <div className="namespace-card-header">
                  <Link to={`/namespaces/${encodeURIComponent(s.namespace.name)}`}>
                    {s.namespace.name}
                  </Link>
                  <ActionMenu
                    items={[
                      {
                        label: 'Edit description',
                        icon: Pencil,
                        onClick: () => setEditing(s.namespace),
                      },
                      {
                        label: 'Delete namespace',
                        icon: Trash2,
                        destructive: true,
                        onClick: () => setDeleting(s.namespace),
                      },
                    ]}
                  />
                </div>
                {s.namespace.description && <p className="muted">{s.namespace.description}</p>}
                <p className="muted small">
                  Created {new Date(s.namespace.created_at).toLocaleString()}
                </p>
                <div className="namespace-card-stats">
                  <span className="badge">{s.entityCount} entities</span>
                  <span className="badge">{s.factCount} facts</span>
                </div>
              </motion.div>
            ))}
          </div>
        </>
      )}

      <CreateNamespaceModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        onCreated={() => {
          showToast('Namespace created')
          refresh()
        }}
      />

      <EditNamespaceModal
        key={editing?.name ?? 'edit-closed'}
        namespace={editing}
        onOpenChange={() => setEditing(null)}
        onUpdated={() => {
          showToast('Namespace updated')
          setEditing(null)
          refresh()
        }}
      />

      <DeleteNamespaceModal
        key={deleting?.name ?? 'delete-closed'}
        namespace={deleting}
        onOpenChange={() => setDeleting(null)}
        onDeleted={() => {
          showToast('Namespace deleted')
          setDeleting(null)
          refresh()
        }}
      />
    </div>
  )
}

function KpiCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Database
  label: string
  value: number
}) {
  return (
    <div className="card kpi-card">
      <Icon size={20} />
      <div>
        <div className="kpi-value">{value}</div>
        <div className="kpi-label">{label}</div>
      </div>
    </div>
  )
}

function CreateNamespaceModal({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!name.trim()) {
      setFormError('Name is required')
      return
    }

    setCreating(true)

    try {
      await createNamespace(name.trim(), description.trim())
      setName('')
      setDescription('')
      onOpenChange(false)
      onCreated()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setFormError(`A namespace named "${name.trim()}" already exists`)
      } else {
        setFormError(err instanceof Error ? err.message : 'Failed to create namespace')
      }
    } finally {
      setCreating(false)
    }
  }

  return (
    <Modal open={open} onOpenChange={onOpenChange} title="New namespace">
      <form onSubmit={handleCreate}>
        <div className="field">
          <label htmlFor="namespace-name">Name</label>
          <input
            id="namespace-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. customer-support"
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="namespace-description">Description (optional)</label>
          <input
            id="namespace-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={creating}>
          {creating ? 'Creating…' : 'Create namespace'}
        </button>
      </form>
    </Modal>
  )
}

function EditNamespaceModal({
  namespace,
  onOpenChange,
  onUpdated,
}: {
  namespace: Namespace | null
  onOpenChange: (open: boolean) => void
  onUpdated: () => void
}) {
  const [description, setDescription] = useState(namespace?.description ?? '')
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    if (!namespace) return

    setSaving(true)
    setFormError(null)

    try {
      await updateNamespace(namespace.name, description.trim() || null)
      onUpdated()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update namespace')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={namespace !== null}
      onOpenChange={onOpenChange}
      title={`Edit ${namespace?.name ?? ''}`}
    >
      <form onSubmit={handleSave}>
        <div className="field">
          <label htmlFor="edit-namespace-description">Description</label>
          <input
            id="edit-namespace-description"
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

function DeleteNamespaceModal({
  namespace,
  onOpenChange,
  onDeleted,
}: {
  namespace: Namespace | null
  onOpenChange: (open: boolean) => void
  onDeleted: () => void
}) {
  const [confirmText, setConfirmText] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [deletingNow, setDeletingNow] = useState(false)

  async function handleDelete(event: FormEvent) {
    event.preventDefault()
    if (!namespace) return

    if (confirmText !== namespace.name) {
      setFormError('Type the namespace name exactly to confirm')
      return
    }

    setDeletingNow(true)
    setFormError(null)

    try {
      await deleteNamespace(namespace.name)
      onDeleted()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete namespace')
    } finally {
      setDeletingNow(false)
    }
  }

  return (
    <Modal
      open={namespace !== null}
      onOpenChange={onOpenChange}
      title={`Delete ${namespace?.name ?? ''}`}
      description="This permanently deletes every entity, fact, regex rule, and commit in this namespace. This cannot be undone."
    >
      <form onSubmit={handleDelete}>
        <div className="field">
          <label htmlFor="confirm-delete-name">
            Type <strong>{namespace?.name}</strong> to confirm
          </label>
          <input
            id="confirm-delete-name"
            value={confirmText}
            onChange={(e) => setConfirmText(e.target.value)}
            autoFocus
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" className="destructive" disabled={deletingNow}>
          {deletingNow ? 'Deleting…' : 'Delete namespace'}
        </button>
      </form>
    </Modal>
  )
}

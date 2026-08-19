import { lazy, Suspense, useEffect, useState, type FormEvent } from 'react'
import { Pencil, Trash2 } from 'lucide-react'
import {
  deleteEntity,
  deleteFact,
  deleteRegexRule,
  getGraph,
  listFacts,
  listRegexRules,
  updateEntity,
  type Entity,
  type Fact,
  type Graph,
} from '../api'
import SidePanel from '../components/SidePanel'
import Modal from '../components/Modal'
import ActionMenu from '../components/ActionMenu'
import { useToast } from '../components/toastContext'

const EntityMiniGraph = lazy(() => import('./EntityMiniGraph'))

interface EntityDetailPanelProps {
  namespace: string
  entity: Entity | null
  onOpenChange: (open: boolean) => void
  onEntityChanged: (updated: Entity) => void
  onEntityDeleted: (entityId: string) => void
}

export default function EntityDetailPanel({
  namespace,
  entity,
  onOpenChange,
  onEntityChanged,
  onEntityDeleted,
}: EntityDetailPanelProps) {
  const [facts, setFacts] = useState<Fact[]>([])
  const [regexRules, setRegexRules] = useState<string[]>([])
  const [graph, setGraph] = useState<Graph | null>(null)
  const [loading, setLoading] = useState(true)
  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    if (!entity) return

    Promise.all([
      listFacts(namespace),
      listRegexRules(namespace, entity.entity_id).catch(() => []),
      getGraph(namespace).catch(() => null),
    ])
      .then(([allFacts, rules, fetchedGraph]) => {
        setFacts(
          allFacts.filter((f) => f.source === entity.entity_id || f.target === entity.entity_id),
        )
        setRegexRules(rules)
        setGraph(fetchedGraph)
      })
      .finally(() => setLoading(false))
  }, [namespace, entity])

  async function handleDeleteFact(factId: string) {
    try {
      await deleteFact(namespace, factId)
      setFacts((current) => current.filter((f) => f.id !== factId))
      showToast('Fact deleted')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete fact', 'error')
    }
  }

  async function handleDeleteRegexRule(pattern: string) {
    if (!entity) return

    try {
      await deleteRegexRule(namespace, entity.entity_id, pattern)
      setRegexRules((current) => current.filter((p) => p !== pattern))
      showToast('Regex rule deleted')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete regex rule', 'error')
    }
  }

  async function handleDeleteEntity() {
    if (!entity) return

    try {
      await deleteEntity(namespace, entity.entity_id)
      showToast('Entity deleted')
      setDeleteOpen(false)
      onEntityDeleted(entity.entity_id)
      onOpenChange(false)
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete entity', 'error')
    }
  }

  return (
    <>
      <SidePanel
        open={entity !== null}
        onOpenChange={onOpenChange}
        title={entity ? `${entity.label} (${entity.entity_id})` : ''}
      >
        {entity && (
          <div>
            <div className="entity-panel-actions">
              <button type="button" onClick={() => setEditOpen(true)}>
                <Pencil size={14} />
                Edit
              </button>
              <button type="button" className="destructive" onClick={() => setDeleteOpen(true)}>
                <Trash2 size={14} />
                Delete
              </button>
            </div>

            <h4>Surface texts</h4>
            <p className="muted small">
              {entity.surface_texts.join(', ') || 'No surface texts'}
            </p>

            <h4>Local graph</h4>
            {graph && (
              <Suspense fallback={<p className="muted small">Loading graph&hellip;</p>}>
                <EntityMiniGraph graph={graph} entityId={entity.entity_id} />
              </Suspense>
            )}

            <h4>Facts</h4>
            {loading && <p className="muted small">Loading&hellip;</p>}
            {!loading && facts.length === 0 && <p className="muted small">No facts yet</p>}
            <ul className="plain-list">
              {facts.map((fact) => (
                <li key={fact.id} className="row-with-menu">
                  <span>
                    {fact.source} --[{fact.predicate}]--&gt; {fact.target}
                  </span>
                  <ActionMenu
                    items={[
                      {
                        label: 'Delete',
                        icon: Trash2,
                        destructive: true,
                        onClick: () => handleDeleteFact(fact.id),
                      },
                    ]}
                  />
                </li>
              ))}
            </ul>

            <h4>Regex rules</h4>
            {!loading && regexRules.length === 0 && <p className="muted small">No regex rules</p>}
            <ul className="plain-list">
              {regexRules.map((pattern) => (
                <li key={pattern} className="row-with-menu">
                  <code>{pattern}</code>
                  <ActionMenu
                    items={[
                      {
                        label: 'Delete',
                        icon: Trash2,
                        destructive: true,
                        onClick: () => handleDeleteRegexRule(pattern),
                      },
                    ]}
                  />
                </li>
              ))}
            </ul>
          </div>
        )}
      </SidePanel>

      <EditEntityModal
        key={entity?.entity_id ?? 'edit-entity-closed'}
        namespace={namespace}
        entity={editOpen ? entity : null}
        onOpenChange={() => setEditOpen(false)}
        onSaved={(updated) => {
          showToast('Entity updated')
          setEditOpen(false)
          onEntityChanged(updated)
        }}
      />

      <Modal
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        title={`Delete ${entity?.entity_id ?? ''}`}
        description="This permanently deletes the entity and every fact referencing it."
      >
        <button type="button" className="destructive" onClick={handleDeleteEntity}>
          <Trash2 size={14} />
          Delete entity
        </button>
      </Modal>
    </>
  )
}

function EditEntityModal({
  namespace,
  entity,
  onOpenChange,
  onSaved,
}: {
  namespace: string
  entity: Entity | null
  onOpenChange: (open: boolean) => void
  onSaved: (updated: Entity) => void
}) {
  const [label, setLabel] = useState(entity?.label ?? '')
  const [surfaceTexts, setSurfaceTexts] = useState(entity?.surface_texts.join(', ') ?? '')
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSave(event: FormEvent) {
    event.preventDefault()
    if (!entity) return

    setSaving(true)
    setFormError(null)

    try {
      const updated = await updateEntity(namespace, entity.entity_id, {
        label,
        surface_texts: surfaceTexts
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      })
      onSaved(updated)
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to update entity')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      open={entity !== null}
      onOpenChange={onOpenChange}
      title={`Edit ${entity?.entity_id ?? ''}`}
    >
      <form onSubmit={handleSave}>
        <div className="field">
          <label htmlFor="edit-entity-label">Label</label>
          <input
            id="edit-entity-label"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="edit-entity-surface-texts">Surface texts (comma-separated)</label>
          <input
            id="edit-entity-surface-texts"
            value={surfaceTexts}
            onChange={(e) => setSurfaceTexts(e.target.value)}
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

import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trash2, Eye } from 'lucide-react'
import {
  addRegexRule,
  addSurfaceText,
  createEntity,
  createFact,
  deleteFact,
  listEntities,
  listFacts,
  type Entity,
  type Fact,
} from '../api'
import { useNamespaceContext } from './namespaceContext'
import { useToast } from '../components/toastContext'
import EntityCombobox from '../components/EntityCombobox'
import ActionMenu from '../components/ActionMenu'
import EntityDetailPanel from '../panels/EntityDetailPanel'

function inspectLink(namespace: string, entityId: string) {
  return `/namespaces/${encodeURIComponent(namespace)}?left=inspect&focus=${encodeURIComponent(entityId)}`
}

export default function NamespaceTrain() {
  const { namespace } = useNamespaceContext()
  const { showToast } = useToast()
  const navigate = useNavigate()

  const [entities, setEntities] = useState<Entity[]>([])
  const [entitiesLoading, setEntitiesLoading] = useState(true)
  const [entitiesError, setEntitiesError] = useState<string | null>(null)

  const [facts, setFacts] = useState<Fact[]>([])
  const [factsLoading, setFactsLoading] = useState(true)
  const [factsError, setFactsError] = useState<string | null>(null)

  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)

  useEffect(() => {
    listEntities(namespace)
      .then(setEntities)
      .catch((err: unknown) => {
        setEntitiesError(err instanceof Error ? err.message : 'Failed to load entities')
      })
      .finally(() => setEntitiesLoading(false))

    listFacts(namespace)
      .then(setFacts)
      .catch((err: unknown) => {
        setFactsError(err instanceof Error ? err.message : 'Failed to load facts')
      })
      .finally(() => setFactsLoading(false))
  }, [namespace])

  async function handleDeleteFact(factId: string) {
    try {
      await deleteFact(namespace, factId)
      setFacts((current) => current.filter((f) => f.id !== factId))
      showToast('Fact deleted')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete fact', 'error')
    }
  }

  return (
    <div className="train-grid">
      <CreateEntityForm
        entities={entities}
        loading={entitiesLoading}
        error={entitiesError}
        onCreated={(entity) => {
          setEntities((current) => [entity, ...current])
          showToast('Entity created', 'success', {
            label: 'View in Inspect',
            onClick: () => navigate(inspectLink(namespace, entity.entity_id)),
          })
        }}
        onSelect={setSelectedEntity}
      />
      <AddSurfaceTextForm
        entities={entities}
        onAdded={(updated) => {
          setEntities((current) =>
            current.map((e) => (e.entity_id === updated.entity_id ? updated : e)),
          )
          showToast('Surface text added')
        }}
      />
      <AddRegexRuleForm entities={entities} />
      <CreateFactForm
        entities={entities}
        facts={facts}
        loading={factsLoading}
        error={factsError}
        onCreated={(fact) => {
          setFacts((current) => [fact, ...current])
          showToast('Fact created', 'success', {
            label: 'View in Inspect',
            onClick: () => navigate(inspectLink(namespace, fact.source)),
          })
        }}
        onDelete={handleDeleteFact}
      />

      <EntityDetailPanel
        key={selectedEntity?.entity_id ?? 'entity-panel-closed'}
        namespace={namespace}
        entity={selectedEntity}
        onOpenChange={() => setSelectedEntity(null)}
        onEntityChanged={(updated) => {
          setEntities((current) =>
            current.map((e) => (e.entity_id === updated.entity_id ? updated : e)),
          )
          setSelectedEntity(updated)
        }}
        onEntityDeleted={(entityId) => {
          setEntities((current) => current.filter((e) => e.entity_id !== entityId))
        }}
      />
    </div>
  )
}

function CreateEntityForm({
  entities,
  loading,
  error,
  onCreated,
  onSelect,
}: {
  entities: Entity[]
  loading: boolean
  error: string | null
  onCreated: (entity: Entity) => void
  onSelect: (entity: Entity) => void
}) {
  const { namespace } = useNamespaceContext()
  const [entityId, setEntityId] = useState('')
  const [label, setLabel] = useState('')
  const [surfaceTexts, setSurfaceTexts] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!entityId.trim()) {
      setFormError('entity_id is required')
      return
    }

    setSubmitting(true)

    try {
      const created = await createEntity(
        namespace,
        entityId.trim(),
        label.trim(),
        surfaceTexts
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      )
      onCreated(created)
      setEntityId('')
      setLabel('')
      setSurfaceTexts('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create entity')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Create entity</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="entity-id">entity_id</label>
          <input id="entity-id" value={entityId} onChange={(e) => setEntityId(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="entity-label">Label (optional)</label>
          <input id="entity-label" value={label} onChange={(e) => setLabel(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="entity-surface-texts">Surface texts (comma-separated)</label>
          <input
            id="entity-surface-texts"
            value={surfaceTexts}
            onChange={(e) => setSurfaceTexts(e.target.value)}
            placeholder="mayank, mayank gupta"
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create entity'}
        </button>
      </form>

      {loading && <p>Loading entities…</p>}
      {error && <p className="error">{error}</p>}
      <ul className="plain-list">
        {entities.map((entity) => (
          <li key={entity.entity_id} className="row-with-menu">
            <button
              type="button"
              className="link-row"
              onClick={() => onSelect(entity)}
            >
              <strong>{entity.entity_id}</strong> ({entity.label}) -{' '}
              {entity.surface_texts.join(', ') || 'no surface texts'}
            </button>
            <ActionMenu
              items={[
                { label: 'View details', icon: Eye, onClick: () => onSelect(entity) },
              ]}
            />
          </li>
        ))}
      </ul>
    </section>
  )
}

function AddSurfaceTextForm({
  entities,
  onAdded,
}: {
  entities: Entity[]
  onAdded: (entity: Entity) => void
}) {
  const { namespace } = useNamespaceContext()
  const [entityId, setEntityId] = useState('')
  const [surfaceText, setSurfaceText] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!entityId || !surfaceText.trim()) {
      setFormError('Pick an entity and enter a surface text')
      return
    }

    setSubmitting(true)

    try {
      const updated = await addSurfaceText(namespace, entityId, surfaceText.trim())
      onAdded(updated)
      setSurfaceText('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to add surface text')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Add surface text</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="surface-text-entity">Entity</label>
          <EntityCombobox entities={entities} value={entityId} onChange={setEntityId} />
        </div>
        <div className="field">
          <label htmlFor="surface-text-value">Surface text</label>
          <input
            id="surface-text-value"
            value={surfaceText}
            onChange={(e) => setSurfaceText(e.target.value)}
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding…' : 'Add surface text'}
        </button>
      </form>
    </section>
  )
}

function AddRegexRuleForm({ entities }: { entities: Entity[] }) {
  const { namespace } = useNamespaceContext()
  const { showToast } = useToast()
  const [entityId, setEntityId] = useState('')
  const [regex, setRegex] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!entityId || !regex.trim()) {
      setFormError('Pick an entity and enter a pattern')
      return
    }

    setSubmitting(true)

    try {
      await addRegexRule(namespace, entityId, regex.trim())
      showToast(`Added regex rule to ${entityId}`)
      setRegex('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to add regex rule')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Add regex rule</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="regex-entity">Entity</label>
          <EntityCombobox entities={entities} value={entityId} onChange={setEntityId} />
        </div>
        <div className="field">
          <label htmlFor="regex-pattern">Pattern</label>
          <input
            id="regex-pattern"
            value={regex}
            onChange={(e) => setRegex(e.target.value)}
            placeholder="\d{4}"
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding…' : 'Add regex rule'}
        </button>
      </form>
    </section>
  )
}

function CreateFactForm({
  entities,
  facts,
  loading,
  error,
  onCreated,
  onDelete,
}: {
  entities: Entity[]
  facts: Fact[]
  loading: boolean
  error: string | null
  onCreated: (fact: Fact) => void
  onDelete: (factId: string) => void
}) {
  const { namespace } = useNamespaceContext()
  const [source, setSource] = useState('')
  const [predicate, setPredicate] = useState('')
  const [target, setTarget] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!source.trim() || !predicate.trim() || !target.trim()) {
      setFormError('source, predicate, and target are all required')
      return
    }

    setSubmitting(true)

    try {
      const created = await createFact(namespace, source.trim(), predicate.trim(), target.trim())
      onCreated(created)
      setSource('')
      setPredicate('')
      setTarget('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to create fact')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Create fact</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="fact-source">Source entity</label>
          <EntityCombobox entities={entities} value={source} onChange={setSource} />
        </div>
        <div className="field">
          <label htmlFor="fact-predicate">Predicate</label>
          <input
            id="fact-predicate"
            value={predicate}
            onChange={(e) => setPredicate(e.target.value)}
            placeholder="FOUNDED_BY"
          />
        </div>
        <div className="field">
          <label htmlFor="fact-target">Target entity</label>
          <EntityCombobox entities={entities} value={target} onChange={setTarget} />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create fact'}
        </button>
      </form>

      {loading && <p>Loading facts…</p>}
      {error && <p className="error">{error}</p>}
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
                  onClick: () => onDelete(fact.id),
                },
              ]}
            />
          </li>
        ))}
      </ul>
    </section>
  )
}

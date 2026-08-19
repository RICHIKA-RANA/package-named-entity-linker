import { useEffect, useState, type FormEvent } from 'react'
import {
  addRegexRule,
  addSurfaceText,
  createEntity,
  createFact,
  listEntities,
  listFacts,
  type Entity,
  type Fact,
} from '../api'
import { useNamespaceContext } from './namespaceContext'

export default function NamespaceTrain() {
  const { namespace } = useNamespaceContext()

  const [entities, setEntities] = useState<Entity[]>([])
  const [entitiesLoading, setEntitiesLoading] = useState(true)
  const [entitiesError, setEntitiesError] = useState<string | null>(null)

  const [facts, setFacts] = useState<Fact[]>([])
  const [factsLoading, setFactsLoading] = useState(true)
  const [factsError, setFactsError] = useState<string | null>(null)

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

  return (
    <div className="train-grid">
      <CreateEntityForm
        entities={entities}
        loading={entitiesLoading}
        error={entitiesError}
        onCreated={(entity) => setEntities((current) => [entity, ...current])}
      />
      <AddSurfaceTextForm
        entities={entities}
        onAdded={(updated) =>
          setEntities((current) =>
            current.map((e) => (e.entity_id === updated.entity_id ? updated : e)),
          )
        }
      />
      <AddRegexRuleForm entities={entities} />
      <CreateFactForm
        facts={facts}
        loading={factsLoading}
        error={factsError}
        onCreated={(fact) => setFacts((current) => [fact, ...current])}
      />
    </div>
  )
}

function CreateEntityForm({
  entities,
  loading,
  error,
  onCreated,
}: {
  entities: Entity[]
  loading: boolean
  error: string | null
  onCreated: (entity: Entity) => void
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
          <li key={entity.entity_id}>
            <strong>{entity.entity_id}</strong> ({entity.label}) -{' '}
            {entity.surface_texts.join(', ') || 'no surface texts'}
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
          <select
            id="surface-text-entity"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
          >
            <option value="">Select an entity…</option>
            {entities.map((entity) => (
              <option key={entity.entity_id} value={entity.entity_id}>
                {entity.entity_id}
              </option>
            ))}
          </select>
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
  const [entityId, setEntityId] = useState('')
  const [regex, setRegex] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)
    setSubmitted(null)

    if (!entityId || !regex.trim()) {
      setFormError('Pick an entity and enter a pattern')
      return
    }

    setSubmitting(true)

    try {
      await addRegexRule(namespace, entityId, regex.trim())
      setSubmitted(`Added regex rule to ${entityId}`)
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
          <select
            id="regex-entity"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
          >
            <option value="">Select an entity…</option>
            {entities.map((entity) => (
              <option key={entity.entity_id} value={entity.entity_id}>
                {entity.entity_id}
              </option>
            ))}
          </select>
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
        {submitted && <p className="muted small">{submitted}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding…' : 'Add regex rule'}
        </button>
      </form>
    </section>
  )
}

function CreateFactForm({
  facts,
  loading,
  error,
  onCreated,
}: {
  facts: Fact[]
  loading: boolean
  error: string | null
  onCreated: (fact: Fact) => void
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
          <label htmlFor="fact-source">Source entity_id</label>
          <input id="fact-source" value={source} onChange={(e) => setSource(e.target.value)} />
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
          <label htmlFor="fact-target">Target entity_id</label>
          <input id="fact-target" value={target} onChange={(e) => setTarget(e.target.value)} />
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
          <li key={fact.id}>
            {fact.source} --[{fact.predicate}]--&gt; {fact.target}
          </li>
        ))}
      </ul>
    </section>
  )
}

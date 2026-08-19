import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, createNamespace, listNamespaces, type Namespace } from '../api'

export default function NamespaceList() {
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    listNamespaces()
      .then(setNamespaces)
      .catch((err: unknown) => {
        setLoadError(err instanceof Error ? err.message : 'Failed to load namespaces')
      })
      .finally(() => setLoading(false))
  }, [])

  async function handleCreate(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    if (!name.trim()) {
      setFormError('Name is required')
      return
    }

    setCreating(true)

    try {
      const created = await createNamespace(name.trim(), description.trim())
      setNamespaces((current) => [created, ...current])
      setName('')
      setDescription('')
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
    <section>
      <h2>Namespaces</h2>

      <form className="card" onSubmit={handleCreate}>
        <div className="field">
          <label htmlFor="namespace-name">Name</label>
          <input
            id="namespace-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. customer-support"
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

      {loading && <p>Loading namespaces…</p>}
      {loadError && <p className="error">{loadError}</p>}

      {!loading && !loadError && namespaces.length === 0 && (
        <p>No namespaces yet - create one above to get started.</p>
      )}

      <ul className="namespace-list">
        {namespaces.map((ns) => (
          <li key={ns.name} className="card">
            <Link to={`/namespaces/${encodeURIComponent(ns.name)}`}>{ns.name}</Link>
            {ns.description && <p className="muted">{ns.description}</p>}
            <p className="muted small">Created {new Date(ns.created_at).toLocaleString()}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getNamespace, type Namespace } from '../api'

const COMING_SOON = ['Train', 'Test', 'History', 'Graph']

// Keyed by `name` in App.tsx so React fully remounts (and state resets
// naturally) when navigating between two different namespaces, rather
// than reusing this instance and resetting loading/error by hand.
function NamespaceDetail({ name }: { name: string }) {
  const [namespace, setNamespace] = useState<Namespace | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getNamespace(name)
      .then(setNamespace)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load namespace')
      })
      .finally(() => setLoading(false))
  }, [name])

  return (
    <section>
      <p>
        <Link to="/">&larr; Back to namespaces</Link>
      </p>

      {loading && <p>Loading…</p>}
      {error && <p className="error">{error}</p>}

      {namespace && (
        <>
          <h2>{namespace.name}</h2>
          {namespace.description && <p className="muted">{namespace.description}</p>}
          <p className="muted small">
            Created {new Date(namespace.created_at).toLocaleString()}
          </p>

          <nav className="tab-nav">
            {COMING_SOON.map((label) => (
              <button key={label} disabled title="Coming soon">
                {label}
              </button>
            ))}
          </nav>
        </>
      )}
    </section>
  )
}

export default function NamespaceDetailRoute() {
  const { name } = useParams<{ name: string }>()

  if (!name) return null

  return <NamespaceDetail key={name} name={name} />
}

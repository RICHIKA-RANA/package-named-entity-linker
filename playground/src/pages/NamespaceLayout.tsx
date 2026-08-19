import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useParams } from 'react-router-dom'
import { getNamespace, type Namespace } from '../api'
import type { NamespaceContext } from './namespaceContext'

function NamespaceLayoutInner({ name }: { name: string }) {
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
            <NavLink to="train">Train</NavLink>
            <NavLink to="test">Test</NavLink>
            <button disabled title="Coming soon">
              History
            </button>
            <button disabled title="Coming soon">
              Graph
            </button>
          </nav>

          <div className="tab-content">
            <Outlet context={{ namespace: name } satisfies NamespaceContext} />
          </div>
        </>
      )}
    </section>
  )
}

export default function NamespaceLayout() {
  const { name } = useParams<{ name: string }>()

  if (!name) return null

  return <NamespaceLayoutInner key={name} name={name} />
}

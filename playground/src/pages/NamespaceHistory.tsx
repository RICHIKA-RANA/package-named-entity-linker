import { useEffect, useState, type FormEvent } from 'react'
import {
  commitNamespace,
  getCommit,
  listCommits,
  rollbackNamespace,
  type Commit,
  type CommitDetail,
} from '../api'
import { useNamespaceContext } from './namespaceContext'

export default function NamespaceHistory() {
  const { namespace } = useNamespaceContext()

  const [commits, setCommits] = useState<Commit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listCommits(namespace)
      .then(setCommits)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load commits')
      })
      .finally(() => setLoading(false))
  }, [namespace])

  return (
    <div>
      <CommitForm onCreated={(commit) => setCommits((current) => [commit, ...current])} />

      <section className="card">
        <h3>Commit history</h3>
        {loading && <p>Loading commits…</p>}
        {error && <p className="error">{error}</p>}
        {!loading && commits.length === 0 && <p className="muted">No commits yet</p>}
        <ul className="plain-list">
          {commits.map((commit) => (
            <CommitRow
              key={commit.commit_id}
              commit={commit}
              onRolledBack={(newCommit) => setCommits((current) => [newCommit, ...current])}
            />
          ))}
        </ul>
      </section>
    </div>
  )
}

function CommitForm({ onCreated }: { onCreated: (commit: Commit) => void }) {
  const { namespace } = useNamespaceContext()
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
      const commit = await commitNamespace(namespace, message.trim())
      onCreated(commit)
      setMessage('')
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to commit')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Commit current state</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="commit-message">Message</label>
          <input
            id="commit-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add mayank entity and greeting facts"
          />
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Committing…' : 'Commit current state'}
        </button>
      </form>
    </section>
  )
}

function CommitRow({
  commit,
  onRolledBack,
}: {
  commit: Commit
  onRolledBack: (commit: Commit) => void
}) {
  const { namespace } = useNamespaceContext()
  const [expanded, setExpanded] = useState(false)
  const [detail, setDetail] = useState<CommitDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<string | null>(null)
  const [rollingBack, setRollingBack] = useState(false)
  const [rollbackError, setRollbackError] = useState<string | null>(null)
  const [rolledBackTo, setRolledBackTo] = useState(false)

  async function handleToggleDetails() {
    const next = !expanded
    setExpanded(next)

    if (next && !detail) {
      setDetailLoading(true)
      setDetailError(null)

      try {
        setDetail(await getCommit(namespace, commit.commit_id))
      } catch (err) {
        setDetailError(err instanceof Error ? err.message : 'Failed to load commit details')
      } finally {
        setDetailLoading(false)
      }
    }
  }

  async function handleRollback() {
    setRollingBack(true)
    setRollbackError(null)

    try {
      const newCommit = await rollbackNamespace(namespace, commit.commit_id)
      onRolledBack(newCommit)
      setRolledBackTo(true)
    } catch (err) {
      setRollbackError(err instanceof Error ? err.message : 'Failed to roll back')
    } finally {
      setRollingBack(false)
    }
  }

  return (
    <li>
      <div className="commit-row">
        <div>
          <code>{commit.commit_id.slice(0, 8)}</code> - {commit.message}
          <p className="muted small">{new Date(commit.created_at).toLocaleString()}</p>
        </div>
        <div className="commit-actions">
          <button type="button" onClick={handleToggleDetails}>
            {expanded ? 'Hide details' : 'Details'}
          </button>
          <button type="button" onClick={handleRollback} disabled={rollingBack}>
            {rollingBack ? 'Rolling back…' : 'Roll back to this commit'}
          </button>
        </div>
      </div>

      {rolledBackTo && <p className="muted small">Rolled back - see the new commit above</p>}
      {rollbackError && <p className="error">{rollbackError}</p>}

      {expanded && (
        <div className="commit-detail">
          {detailLoading && <p>Loading details…</p>}
          {detailError && <p className="error">{detailError}</p>}
          {detail && (
            <>
              <p className="muted small">
                {detail.snapshot.entities.nodes.length} entities,{' '}
                {detail.snapshot.entities.edges.length} facts,{' '}
                {Object.keys(detail.snapshot.regex_rules).length} regex rule sets
              </p>
              <details>
                <summary>Raw snapshot JSON</summary>
                <pre className="commit-snapshot">{JSON.stringify(detail.snapshot, null, 2)}</pre>
              </details>
            </>
          )}
        </div>
      )}
    </li>
  )
}

import { useEffect, useState, type FormEvent } from 'react'
import { commitNamespace, listCommits, type Commit } from '../api'
import { useNamespaceContext } from './namespaceContext'
import CommitDetailPanel from '../panels/CommitDetailPanel'

export default function NamespaceHistory() {
  const { namespace } = useNamespaceContext()

  const [commits, setCommits] = useState<Commit[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedCommit, setSelectedCommit] = useState<Commit | null>(null)

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
            <li key={commit.commit_id}>
              <div className="commit-row">
                <div>
                  <code>{commit.commit_id.slice(0, 8)}</code> - {commit.message}
                  <p className="muted small">{new Date(commit.created_at).toLocaleString()}</p>
                </div>
                <div className="commit-actions">
                  <button type="button" onClick={() => setSelectedCommit(commit)}>
                    Details
                  </button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <CommitDetailPanel
        key={selectedCommit?.commit_id ?? 'commit-panel-closed'}
        namespace={namespace}
        commit={selectedCommit}
        onOpenChange={() => setSelectedCommit(null)}
        onRolledBack={(newCommit) => setCommits((current) => [newCommit, ...current])}
      />
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

import { useEffect, useState } from 'react'
import { listCommits, type Commit } from '../api'
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
      <section className="card">
        <h3>Commit history</h3>
        <p className="muted small">
          Use the Commit button at the top of the workspace to snapshot the current state.
        </p>
        {loading && <p>Loading commits…</p>}
        {error && <p className="error">{error}</p>}
        {!loading && commits.length === 0 && <p className="muted">No commits yet</p>}
        <ul className="plain-list">
          {commits.map((commit, index) => (
            <li key={commit.commit_id}>
              <div className="commit-row">
                <div>
                  <code>{commit.commit_id.slice(0, 8)}</code> - {commit.message}
                  {index === 0 && <span className="badge current-badge">Current</span>}
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

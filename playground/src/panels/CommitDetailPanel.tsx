import { useEffect, useState } from 'react'
import { History } from 'lucide-react'
import { getCommit, rollbackNamespace, type Commit, type CommitDetail } from '../api'
import SidePanel from '../components/SidePanel'
import { useToast } from '../components/toastContext'

interface CommitDetailPanelProps {
  namespace: string
  commit: Commit | null
  onOpenChange: (open: boolean) => void
  onRolledBack: (newCommit: Commit) => void
}

export default function CommitDetailPanel({
  namespace,
  commit,
  onOpenChange,
  onRolledBack,
}: CommitDetailPanelProps) {
  const [detail, setDetail] = useState<CommitDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rollingBack, setRollingBack] = useState(false)
  const [rolledBack, setRolledBack] = useState(false)
  const { showToast } = useToast()

  useEffect(() => {
    if (!commit) return

    getCommit(namespace, commit.commit_id)
      .then(setDetail)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load commit details')
      })
      .finally(() => setLoading(false))
  }, [namespace, commit])

  async function handleRollback() {
    if (!commit) return

    setRollingBack(true)

    try {
      const newCommit = await rollbackNamespace(namespace, commit.commit_id)
      onRolledBack(newCommit)
      setRolledBack(true)
      showToast('Rolled back to this commit')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to roll back', 'error')
    } finally {
      setRollingBack(false)
    }
  }

  return (
    <SidePanel
      open={commit !== null}
      onOpenChange={onOpenChange}
      title={commit ? `Commit ${commit.commit_id.slice(0, 8)}` : ''}
    >
      {commit && (
        <div>
          <p className="muted small">{commit.message}</p>
          <p className="muted small">{new Date(commit.created_at).toLocaleString()}</p>

          {loading && <p>Loading&hellip;</p>}
          {error && <p className="error">{error}</p>}

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

          <div className="side-panel-action">
            <button type="button" onClick={handleRollback} disabled={rollingBack}>
              <History size={14} />
              {rollingBack ? 'Rolling back…' : 'Roll back to this commit'}
            </button>
          </div>

          {rolledBack && (
            <p className="muted small">Rolled back - see the new commit at the top of history</p>
          )}
        </div>
      )}
    </SidePanel>
  )
}

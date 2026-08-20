import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Play, Upload, Download, Check, X as XIcon, Trash2 } from 'lucide-react'
import {
  acceptTestCase,
  bulkCreateEntities,
  bulkCreateTestCases,
  createTestCase,
  createTestRun,
  deleteTestCase,
  getTestRunResults,
  listTestCases,
  listTestRuns,
  rejectTestCase,
  runExtraction,
  type ExtractionResult,
  type TestCase,
  type TestRun,
  type TestRunResult,
  type TestRunSummary,
} from '../api'
import { useNamespaceContext } from './namespaceContext'
import { useToast } from '../components/toastContext'
import ActionMenu from '../components/ActionMenu'
import HighlightedText from '../components/HighlightedText'
import type { HighlightSpan } from '../highlight'
import { computeAccuracyTrend, type AccuracyPoint } from '../charts/accuracyTrend'
import AccuracyTrendChart from '../charts/AccuracyTrendChart'

function buildSpans(result: ExtractionResult): HighlightSpan[] {
  return [
    ...result.universal_entities.map((match) => ({
      start: match.index[0],
      end: match.index[1],
      kind: 'entity',
      label: match.entities.map((e) => `${e.label} (${e.entity_id})`).join(', '),
    })),
    ...result.regex_entities.map((match) => ({
      start: match.index[0],
      end: match.index[1],
      kind: 'regex',
      label: `rule: ${match.rule}`,
    })),
  ]
}

const STATUS_LABELS: Record<string, string> = {
  pass: 'Pass',
  regression: 'Regression',
  fixed: 'Fixed',
  fail: 'Fail',
  new: 'New',
  needs_review: 'Needs review',
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`status-badge status-${status}`}>{STATUS_LABELS[status] ?? status}</span>
  )
}

const ENTITIES_CSV_TEMPLATE = 'entity_id,label,surface_texts\nacme,Acme Corp,acme|acme corp\n'
const ENTITIES_JSON_TEMPLATE = JSON.stringify(
  [{ entity_id: 'acme', label: 'Acme Corp', surface_texts: ['acme', 'acme corp'] }],
  null,
  2,
)
const TEST_CASES_CSV_TEMPLATE =
  'message_text,word_correction,expected\n' +
  'mayank works at acme,false,"[{""surface_text"": ""mayank"", ""entity_id"": ""mayank""}]"\n' +
  'unlabeled example query,false,\n'
const TEST_CASES_JSON_TEMPLATE = JSON.stringify(
  [
    {
      message_text: 'mayank works at acme',
      word_correction: false,
      expected: [{ surface_text: 'mayank', entity_id: 'mayank' }],
    },
    { message_text: 'unlabeled example query', word_correction: false },
  ],
  null,
  2,
)

function downloadTemplate(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export default function NamespaceTests() {
  const { namespace } = useNamespaceContext()
  const { showToast } = useToast()

  const [cases, setCases] = useState<TestCase[]>([])
  const [casesLoading, setCasesLoading] = useState(true)
  const [runs, setRuns] = useState<TestRun[]>([])
  const [trend, setTrend] = useState<AccuracyPoint[]>([])
  const [latestSummary, setLatestSummary] = useState<TestRunSummary | null>(null)
  const [running, setRunning] = useState(false)

  async function refreshCases() {
    setCasesLoading(true)
    try {
      setCases(await listTestCases(namespace))
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to load test cases', 'error')
    } finally {
      setCasesLoading(false)
    }
  }

  async function refreshRuns() {
    try {
      const list = await listTestRuns(namespace)
      setRuns(list)

      const resultsByRun: Record<string, TestRunResult[]> = {}
      await Promise.all(
        list.map(async (run) => {
          resultsByRun[run.id] = await getTestRunResults(namespace, run.id)
        }),
      )
      setTrend(computeAccuracyTrend(list, resultsByRun))
    } catch {
      // run history is supplementary - failures here don't block the page
    }
  }

  useEffect(() => {
    refreshCases()
    refreshRuns()
    // Mount-only: this whole subtree already remounts on namespace change
    // via NamespaceWorkspace's key={name}, so there's no "reset on prop
    // change" case to handle here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleRun() {
    setRunning(true)

    try {
      const summary = await createTestRun(namespace)
      setLatestSummary(summary)
      showToast(
        summary.accuracy !== null
          ? `Run complete: ${Math.round(summary.accuracy * 100)}% accuracy`
          : 'Run complete: no graded cases yet',
      )
      await Promise.all([refreshCases(), refreshRuns()])
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to run tests', 'error')
    } finally {
      setRunning(false)
    }
  }

  async function handleAccept(testCaseId: string) {
    try {
      const updated = await acceptTestCase(namespace, testCaseId)
      setCases((current) => current.map((c) => (c.id === testCaseId ? updated : c)))
      showToast('Accepted')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to accept', 'error')
    }
  }

  async function handleReject(testCaseId: string) {
    try {
      const updated = await rejectTestCase(namespace, testCaseId)
      setCases((current) => current.map((c) => (c.id === testCaseId ? updated : c)))
      showToast('Rejected')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to reject', 'error')
    }
  }

  async function handleDeleteCase(testCaseId: string) {
    try {
      await deleteTestCase(namespace, testCaseId)
      setCases((current) => current.filter((c) => c.id !== testCaseId))
      showToast('Test case deleted')
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Failed to delete test case', 'error')
    }
  }

  const caseById = new Map(cases.map((c) => [c.id, c]))

  return (
    <div>
      <UploadSection onUploaded={refreshCases} />
      <QuickAddForm onCreated={refreshCases} />

      <section className="card">
        <div className="dashboard-header">
          <h3>Run test suite</h3>
          <button type="button" onClick={handleRun} disabled={running}>
            <Play size={14} />
            {running ? 'Running…' : 'Run tests'}
          </button>
        </div>

        {latestSummary && (
          <div className="accuracy-summary">
            <span className="accuracy-value">
              {latestSummary.accuracy !== null
                ? `${Math.round(latestSummary.accuracy * 100)}%`
                : '—'}
            </span>
            <span className="muted small">
              {latestSummary.passed_count}/{latestSummary.graded_count} graded cases passed
              {latestSummary.total_count > latestSummary.graded_count &&
                ` (${latestSummary.total_count - latestSummary.graded_count} need review)`}
            </span>
          </div>
        )}

        {latestSummary && (
          <ul className="plain-list">
            {latestSummary.results.map((result) => {
              const testCase = caseById.get(result.test_case_id)
              return (
                <li key={result.id} className="row-with-menu">
                  <div>
                    <StatusBadge status={result.status_label} />{' '}
                    <span>{testCase?.message_text ?? result.test_case_id}</span>
                  </div>
                  {result.status_label === 'needs_review' && (
                    <div className="commit-actions">
                      <button type="button" onClick={() => handleAccept(result.test_case_id)}>
                        <Check size={14} />
                        Accept
                      </button>
                      <button type="button" onClick={() => handleReject(result.test_case_id)}>
                        <XIcon size={14} />
                        Reject
                      </button>
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </section>

      {runs.length > 0 && (
        <section className="card">
          <h3>Accuracy trend</h3>
          <AccuracyTrendChart data={trend} />
          <ul className="plain-list">
            {runs.map((run) => (
              <li key={run.id}>
                {new Date(run.created_at).toLocaleString()}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card">
        <h3>Test cases</h3>
        {casesLoading && <p>Loading test cases…</p>}
        {!casesLoading && cases.length === 0 && <p className="muted">No test cases yet</p>}
        <ul className="plain-list">
          {cases.map((testCase) => (
            <li key={testCase.id} className="row-with-menu">
              <div>
                <span>{testCase.message_text}</span>{' '}
                <span className="muted small">
                  {testCase.expected ? `${testCase.expected.length} expected` : 'unlabeled'} -{' '}
                  {testCase.review_status}
                </span>
              </div>
              <ActionMenu
                items={[
                  {
                    label: 'Delete',
                    icon: Trash2,
                    destructive: true,
                    onClick: () => handleDeleteCase(testCase.id),
                  },
                ]}
              />
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function UploadSection({ onUploaded }: { onUploaded: () => void }) {
  const { namespace } = useNamespaceContext()
  const { showToast } = useToast()
  const entityFileRef = useRef<HTMLInputElement>(null)
  const testCaseFileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  async function handleUpload(file: File, kind: 'entities' | 'test-cases') {
    const format = file.name.toLowerCase().endsWith('.csv') ? 'csv' : 'json'
    const content = await file.text()

    setUploading(true)

    try {
      const result =
        kind === 'entities'
          ? await bulkCreateEntities(namespace, format, content)
          : await bulkCreateTestCases(namespace, format, content)

      showToast(
        `${result.created} created` +
          (result.errors.length ? `, ${result.errors.length} errors` : ''),
        result.errors.length ? 'error' : 'success',
      )
      onUploaded()
    } catch (err) {
      showToast(err instanceof Error ? err.message : 'Upload failed', 'error')
    } finally {
      setUploading(false)
    }
  }

  return (
    <section className="card">
      <h3>Bulk upload</h3>
      <div className="upload-row">
        <div>
          <p className="muted small">Training data (entities)</p>
          <div className="upload-actions">
            <button
              type="button"
              onClick={() =>
                downloadTemplate('entities-template.csv', ENTITIES_CSV_TEMPLATE, 'text/csv')
              }
            >
              <Download size={14} />
              CSV template
            </button>
            <button
              type="button"
              onClick={() =>
                downloadTemplate(
                  'entities-template.json',
                  ENTITIES_JSON_TEMPLATE,
                  'application/json',
                )
              }
            >
              <Download size={14} />
              JSON template
            </button>
            <button
              type="button"
              onClick={() => entityFileRef.current?.click()}
              disabled={uploading}
            >
              <Upload size={14} />
              Upload
            </button>
            <input
              ref={entityFileRef}
              type="file"
              accept=".csv,.json"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleUpload(file, 'entities')
                e.target.value = ''
              }}
            />
          </div>
        </div>

        <div>
          <p className="muted small">Test queries</p>
          <div className="upload-actions">
            <button
              type="button"
              onClick={() =>
                downloadTemplate(
                  'test-cases-template.csv',
                  TEST_CASES_CSV_TEMPLATE,
                  'text/csv',
                )
              }
            >
              <Download size={14} />
              CSV template
            </button>
            <button
              type="button"
              onClick={() =>
                downloadTemplate(
                  'test-cases-template.json',
                  TEST_CASES_JSON_TEMPLATE,
                  'application/json',
                )
              }
            >
              <Download size={14} />
              JSON template
            </button>
            <button
              type="button"
              onClick={() => testCaseFileRef.current?.click()}
              disabled={uploading}
            >
              <Upload size={14} />
              Upload
            </button>
            <input
              ref={testCaseFileRef}
              type="file"
              accept=".csv,.json"
              style={{ display: 'none' }}
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) handleUpload(file, 'test-cases')
                e.target.value = ''
              }}
            />
          </div>
        </div>
      </div>
    </section>
  )
}

function QuickAddForm({ onCreated }: { onCreated: () => void }) {
  const { namespace } = useNamespaceContext()
  const [messageText, setMessageText] = useState('')
  const [wordCorrection, setWordCorrection] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [preview, setPreview] = useState<{ text: string; result: ExtractionResult } | null>(null)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setFormError(null)

    const trimmed = messageText.trim()

    if (!trimmed) {
      setFormError('Enter a message to test')
      return
    }

    setSubmitting(true)

    try {
      const [, result] = await Promise.all([
        createTestCase(namespace, trimmed, wordCorrection),
        runExtraction(namespace, trimmed, wordCorrection),
      ])
      setPreview({ text: trimmed, result })
      setMessageText('')
      onCreated()
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to add test case')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card">
      <h3>Add a test case</h3>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="test-case-message">Message text</label>
          <textarea
            id="test-case-message"
            rows={2}
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
          />
        </div>
        <div className="field field-checkbox">
          <label>
            <input
              type="checkbox"
              checked={wordCorrection}
              onChange={(e) => setWordCorrection(e.target.checked)}
            />
            Word correction (fuzzy typo matching)
          </label>
        </div>
        {formError && <p className="error">{formError}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Adding…' : 'Add + preview'}
        </button>
      </form>
      <p className="muted small">
        New test cases start unlabeled - run the suite, then accept or reject the actual result
        to establish expected output.
      </p>

      {preview && (
        <div className="quick-add-preview">
          <h4>Immediate preview</h4>
          <HighlightedText text={preview.text} spans={buildSpans(preview.result)} />
        </div>
      )}
    </section>
  )
}

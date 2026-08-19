import { useState, type FormEvent } from 'react'
import HighlightedText from '../components/HighlightedText'
import { runExtraction, type ExtractionResult } from '../api'
import type { HighlightSpan } from '../highlight'
import { useNamespaceContext } from './namespaceContext'

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

export default function NamespaceTest() {
  const { namespace } = useNamespaceContext()
  const [messageText, setMessageText] = useState('')
  const [wordCorrection, setWordCorrection] = useState(false)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (!messageText.trim()) {
      setError('Enter some text to test')
      return
    }

    setSubmitting(true)

    try {
      setResult(await runExtraction(namespace, messageText, wordCorrection))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Extraction failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <section className="card">
        <h3>Test extraction</h3>
        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="message-text">Message text</label>
            <textarea
              id="message-text"
              rows={4}
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
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={submitting}>
            {submitting ? 'Running…' : 'Run extraction'}
          </button>
        </form>
      </section>

      {result && (
        <section className="card">
          <h3>Result</h3>
          <HighlightedText text={messageText} spans={buildSpans(result)} />

          <h4>Matches</h4>
          <ul className="plain-list">
            {result.universal_entities.map((match, index) => (
              <li key={`u-${index}`}>
                <span className="highlight-entity">{match.surface_text}</span> &rarr;{' '}
                <strong>{match.corrected_text}</strong> (score {match.score}) -{' '}
                {match.entities.map((e) => `${e.label} (${e.entity_id})`).join(', ')}
              </li>
            ))}
            {result.regex_entities.map((match, index) => (
              <li key={`r-${index}`}>
                <span className="highlight-regex">{match.surface_text}</span> - rule: {match.rule}
              </li>
            ))}
            {result.universal_entities.length === 0 && result.regex_entities.length === 0 && (
              <li className="muted">No matches</li>
            )}
          </ul>

          {result.no_tag_entities.length > 0 && (
            <>
              <h4>Unmatched</h4>
              <p className="muted small">
                {result.no_tag_entities.map((tag) => tag.surface_text).join(', ')}
              </p>
            </>
          )}
        </section>
      )}
    </div>
  )
}

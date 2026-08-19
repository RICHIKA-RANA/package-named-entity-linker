import { useMemo, useState } from 'react'
import { buildSnippets } from '../snippets'
import { useNamespaceContext } from './namespaceContext'

type Language = 'js' | 'python'

export default function NamespaceCode() {
  const { namespace } = useNamespaceContext()
  const [language, setLanguage] = useState<Language>('js')

  const snippets = useMemo(
    () => buildSnippets(namespace, window.location.origin),
    [namespace],
  )

  return (
    <div>
      <div className="code-lang-toggle">
        <button
          type="button"
          className={language === 'js' ? 'active' : ''}
          onClick={() => setLanguage('js')}
        >
          JavaScript
        </button>
        <button
          type="button"
          className={language === 'python' ? 'active' : ''}
          onClick={() => setLanguage('python')}
        >
          Python
        </button>
      </div>

      {snippets.map((snippet) => (
        <SnippetCard key={snippet.key} snippet={snippet} language={language} />
      ))}
    </div>
  )
}

function SnippetCard({
  snippet,
  language,
}: {
  snippet: ReturnType<typeof buildSnippets>[number]
  language: Language
}) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'failed'>('idle')

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(snippet[language])
      setCopyState('copied')
    } catch {
      setCopyState('failed')
    } finally {
      setTimeout(() => setCopyState('idle'), 1500)
    }
  }

  return (
    <section className="card">
      <h3>{snippet.title}</h3>
      <p className="muted small">
        {snippet.method} {snippet.path}
      </p>
      <pre className="code-block">{snippet[language]}</pre>
      <button type="button" onClick={handleCopy}>
        {copyState === 'copied' ? 'Copied!' : copyState === 'failed' ? 'Copy failed' : 'Copy'}
      </button>
    </section>
  )
}

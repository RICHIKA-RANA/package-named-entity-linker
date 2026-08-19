import { describe, expect, it } from 'vitest'
import { buildSnippets } from './snippets'

const BASE_URL = 'http://localhost:8092'

describe('buildSnippets', () => {
  it('returns one entry per core action, each with both js and python', () => {
    const snippets = buildSnippets('acme-corp', BASE_URL)

    expect(snippets).toHaveLength(6)
    snippets.forEach((snippet) => {
      expect(snippet.js.length).toBeGreaterThan(0)
      expect(snippet.python.length).toBeGreaterThan(0)
    })
  })

  it('interpolates the namespace into every generated URL', () => {
    const snippets = buildSnippets('acme-corp', BASE_URL)

    snippets.forEach((snippet) => {
      expect(snippet.js).toContain('/api/namespaces/acme-corp/')
      expect(snippet.python).toContain('/api/namespaces/acme-corp/')
    })
  })

  it('url-encodes a namespace with special characters', () => {
    const snippets = buildSnippets('my namespace', BASE_URL)
    const listEntities = snippets.find((s) => s.key === 'list-entities')

    expect(listEntities?.js).toContain('/api/namespaces/my%20namespace/entities')
  })

  it('interpolates the entity_id placeholder for entity-scoped endpoints', () => {
    const snippets = buildSnippets('acme-corp', BASE_URL)
    const addSurfaceText = snippets.find((s) => s.key === 'add-surface-text')

    expect(addSurfaceText?.path).toBe('/api/namespaces/acme-corp/entities/acme/surface-texts')
    expect(addSurfaceText?.js).toContain('/entities/acme/surface-texts')
  })

  it('nests fact attributes as an object rather than flattening them', () => {
    const snippets = buildSnippets('acme-corp', BASE_URL)
    const createFact = snippets.find((s) => s.key === 'create-fact')

    expect(createFact?.js).toContain('attributes: {}')
    expect(createFact?.python).toContain('"attributes": {}')
  })

  it('uses the given base url for every request', () => {
    const snippets = buildSnippets('acme-corp', 'https://example.test')

    snippets.forEach((snippet) => {
      expect(snippet.js).toContain('https://example.test/api/namespaces/acme-corp/')
    })
  })
})

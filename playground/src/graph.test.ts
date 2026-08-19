import { describe, expect, it } from 'vitest'
import { toFlowElements } from './graph'
import type { Graph } from './api'

function makeGraph(overrides: Partial<Graph> = {}): Graph {
  return {
    directed: true,
    multigraph: true,
    nodes: [],
    edges: [],
    ...overrides,
  }
}

describe('toFlowElements', () => {
  it('returns no nodes or edges for an empty graph', () => {
    expect(toFlowElements(makeGraph())).toEqual({ nodes: [], edges: [] })
  })

  it('maps a single node with a label combining label and id', () => {
    const graph = makeGraph({
      nodes: [{ id: 'mayank', label: 'Mayank', surface_texts: ['mayank'] }],
    })

    expect(toFlowElements(graph).nodes).toEqual([
      { id: 'mayank', position: { x: 0, y: 0 }, data: { label: 'Mayank (mayank)' } },
    ])
  })

  it('falls back to the bare id when a node has no label (implicitly created by a fact)', () => {
    const graph = makeGraph({ nodes: [{ id: 'acme', surface_texts: [] }] })

    expect(toFlowElements(graph).nodes).toEqual([
      { id: 'acme', position: { x: 0, y: 0 }, data: { label: 'acme' } },
    ])
  })

  it('maps an edge between two nodes with the predicate as its label', () => {
    const graph = makeGraph({
      nodes: [
        { id: 'mayank', label: 'Mayank', surface_texts: [] },
        { id: 'acme', label: 'Acme', surface_texts: [] },
      ],
      edges: [{ source: 'mayank', target: 'acme', key: 'fact-1', predicate: 'WORKS_AT' }],
    })

    expect(toFlowElements(graph).edges).toEqual([
      { id: 'fact-1', source: 'mayank', target: 'acme', label: 'WORKS_AT' },
    ])
  })

  it('maps multiple edges between the same node pair, keyed by fact id', () => {
    const graph = makeGraph({
      nodes: [
        { id: 'mayank', label: 'Mayank', surface_texts: [] },
        { id: 'acme', label: 'Acme', surface_texts: [] },
      ],
      edges: [
        { source: 'mayank', target: 'acme', key: 'fact-1', predicate: 'WORKS_AT' },
        { source: 'mayank', target: 'acme', key: 'fact-2', predicate: 'FOUNDED' },
      ],
    })

    expect(toFlowElements(graph).edges).toEqual([
      { id: 'fact-1', source: 'mayank', target: 'acme', label: 'WORKS_AT' },
      { id: 'fact-2', source: 'mayank', target: 'acme', label: 'FOUNDED' },
    ])
  })
})

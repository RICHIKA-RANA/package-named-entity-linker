import { describe, expect, it } from 'vitest'
import {
  countFactsByEntity,
  filterEntities,
  matchesQuery,
  shouldDefaultToGraph,
  GRAPH_NODE_THRESHOLD,
} from './inspect'
import type { Entity } from '../api'

function makeEntity(overrides: Partial<Entity> = {}): Entity {
  return { entity_id: 'mayank', label: 'Mayank', surface_texts: ['mayank'], ...overrides }
}

describe('matchesQuery', () => {
  it('matches an empty query against anything', () => {
    expect(matchesQuery(makeEntity(), '')).toBe(true)
    expect(matchesQuery(makeEntity(), '   ')).toBe(true)
  })

  it('matches case-insensitively against entity_id, label, and surface texts', () => {
    const entity = makeEntity({ entity_id: 'acme', label: 'Acme Corp', surface_texts: ['acme inc'] })

    expect(matchesQuery(entity, 'ACME')).toBe(true)
    expect(matchesQuery(entity, 'corp')).toBe(true)
    expect(matchesQuery(entity, 'inc')).toBe(true)
    expect(matchesQuery(entity, 'nope')).toBe(false)
  })
})

describe('filterEntities', () => {
  it('keeps only entities matching the query', () => {
    const entities = [makeEntity({ entity_id: 'acme' }), makeEntity({ entity_id: 'globex' })]

    expect(filterEntities(entities, 'globex').map((e) => e.entity_id)).toEqual(['globex'])
  })
})

describe('countFactsByEntity', () => {
  it('counts a fact toward both its source and target', () => {
    const counts = countFactsByEntity([{ source: 'mayank', target: 'acme' }])

    expect(counts.get('mayank')).toBe(1)
    expect(counts.get('acme')).toBe(1)
  })

  it('does not double-count a self-referencing fact', () => {
    const counts = countFactsByEntity([{ source: 'acme', target: 'acme' }])

    expect(counts.get('acme')).toBe(1)
  })

  it('accumulates across multiple facts touching the same entity', () => {
    const counts = countFactsByEntity([
      { source: 'mayank', target: 'acme' },
      { source: 'mayank', target: 'globex' },
    ])

    expect(counts.get('mayank')).toBe(2)
  })
})

describe('shouldDefaultToGraph', () => {
  it('defaults to graph view when there is at least one node and not too many', () => {
    expect(shouldDefaultToGraph(1)).toBe(true)
    expect(shouldDefaultToGraph(GRAPH_NODE_THRESHOLD)).toBe(true)
  })

  it('defaults to table view when there are no nodes or too many', () => {
    expect(shouldDefaultToGraph(0)).toBe(false)
    expect(shouldDefaultToGraph(GRAPH_NODE_THRESHOLD + 1)).toBe(false)
  })
})

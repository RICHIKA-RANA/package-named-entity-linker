import type { Entity } from '../api'

export const TABLE_ROW_CAP = 200
export const GRAPH_NODE_THRESHOLD = 150

export function matchesQuery(entity: Entity, query: string): boolean {
  const q = query.trim().toLowerCase()
  if (!q) return true

  if (entity.entity_id.toLowerCase().includes(q)) return true
  if (entity.label.toLowerCase().includes(q)) return true
  return entity.surface_texts.some((text) => text.toLowerCase().includes(q))
}

export function filterEntities(entities: Entity[], query: string): Entity[] {
  return entities.filter((entity) => matchesQuery(entity, query))
}

export function countFactsByEntity(facts: { source: string; target: string }[]): Map<string, number> {
  const counts = new Map<string, number>()

  facts.forEach((fact) => {
    counts.set(fact.source, (counts.get(fact.source) ?? 0) + 1)
    if (fact.target !== fact.source) {
      counts.set(fact.target, (counts.get(fact.target) ?? 0) + 1)
    }
  })

  return counts
}

export function shouldDefaultToGraph(nodeCount: number): boolean {
  return nodeCount > 0 && nodeCount <= GRAPH_NODE_THRESHOLD
}

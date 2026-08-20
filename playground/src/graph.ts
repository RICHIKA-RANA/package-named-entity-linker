import type { Edge, Node } from '@xyflow/react'
import type { Graph } from './api'

export function filterToNeighborhood(graph: Graph, entityId: string): Graph {
  const edges = graph.edges.filter(
    (edge) => edge.source === entityId || edge.target === entityId,
  )

  const neighborIds = new Set<string>([entityId])
  edges.forEach((edge) => {
    neighborIds.add(edge.source)
    neighborIds.add(edge.target)
  })

  return {
    directed: graph.directed,
    multigraph: graph.multigraph,
    nodes: graph.nodes.filter((node) => neighborIds.has(node.id)),
    edges,
  }
}

export function toFlowElements(graph: Graph): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = graph.nodes.map((node) => ({
    id: node.id,
    position: { x: 0, y: 0 },
    data: { label: node.label ? `${node.label} (${node.id})` : node.id },
  }))

  const edges: Edge[] = graph.edges.map((edge) => ({
    id: edge.key,
    source: edge.source,
    target: edge.target,
    label: edge.predicate,
  }))

  return { nodes, edges }
}

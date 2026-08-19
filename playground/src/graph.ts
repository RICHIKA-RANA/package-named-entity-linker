import type { Edge, Node } from '@xyflow/react'
import type { Graph } from './api'

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

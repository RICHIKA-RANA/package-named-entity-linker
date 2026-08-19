import { useEffect, useMemo, useState } from 'react'
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  type Edge,
  type Node,
} from '@xyflow/react'
import dagre from 'dagre'
import '@xyflow/react/dist/style.css'
import { getGraph, type Graph } from '../api'
import { toFlowElements } from '../graph'
import { useNamespaceContext } from './namespaceContext'

const NODE_WIDTH = 172
const NODE_HEIGHT = 36

function applyDagreLayout(nodes: Node[], edges: Edge[]): Node[] {
  const layoutGraph = new dagre.graphlib.Graph()
  layoutGraph.setDefaultEdgeLabel(() => ({}))
  layoutGraph.setGraph({ rankdir: 'LR' })

  nodes.forEach((node) => {
    layoutGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT })
  })
  edges.forEach((edge) => {
    layoutGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(layoutGraph)

  return nodes.map((node) => {
    const { x, y } = layoutGraph.node(node.id)
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
  })
}

function GraphCanvas({ graph }: { graph: Graph }) {
  const { nodes, edges } = useMemo(() => {
    const flow = toFlowElements(graph)
    return { nodes: applyDagreLayout(flow.nodes, flow.edges), edges: flow.edges }
  }, [graph])

  return (
    <div className="graph-canvas">
      <ReactFlowProvider>
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}

export default function NamespaceGraph() {
  const { namespace } = useNamespaceContext()
  const [graph, setGraph] = useState<Graph | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getGraph(namespace)
      .then(setGraph)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load graph')
      })
      .finally(() => setLoading(false))
  }, [namespace])

  return (
    <div className="graph-page">
      {loading && <p>Loading graph…</p>}
      {error && <p className="error">{error}</p>}
      {graph && graph.nodes.length === 0 && (
        <p className="muted">No entities yet - add some on the Train tab.</p>
      )}
      {graph && graph.nodes.length > 0 && <GraphCanvas graph={graph} />}
    </div>
  )
}

import { ReactFlow, ReactFlowProvider, Background, Controls } from '@xyflow/react'
import dagre from 'dagre'
import '@xyflow/react/dist/style.css'
import type { Graph } from '../api'
import { filterToNeighborhood, toFlowElements } from '../graph'

const NODE_WIDTH = 150
const NODE_HEIGHT = 32

export default function EntityMiniGraph({ graph, entityId }: { graph: Graph; entityId: string }) {
  const neighborhood = filterToNeighborhood(graph, entityId)
  const flow = toFlowElements(neighborhood)

  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR' })

  flow.nodes.forEach((node) => g.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }))
  flow.edges.forEach((edge) => g.setEdge(edge.source, edge.target))

  dagre.layout(g)

  const nodes = flow.nodes.map((node) => {
    const { x, y } = g.node(node.id)
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - NODE_HEIGHT / 2 } }
  })

  if (nodes.length === 0) {
    return <p className="muted small">No connections yet</p>
  }

  return (
    <div className="entity-mini-graph">
      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={flow.edges}
          fitView
          nodesDraggable={false}
          nodesConnectable={false}
        >
          <Background />
          <Controls showInteractive={false} />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}

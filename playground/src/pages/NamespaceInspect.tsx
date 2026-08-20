import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
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
import { Search, LayoutGrid, Share2 } from 'lucide-react'
import { getGraph, listEntities, listFacts, type Entity, type Fact, type Graph } from '../api'
import { toFlowElements } from '../graph'
import { useNamespaceContext } from './namespaceContext'
import EntityDetailPanel from '../panels/EntityDetailPanel'
import {
  GRAPH_NODE_THRESHOLD,
  TABLE_ROW_CAP,
  countFactsByEntity,
  filterEntities,
  shouldDefaultToGraph,
} from './inspect'

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

function GraphCanvas({
  graph,
  onNodeClick,
}: {
  graph: Graph
  onNodeClick: (entityId: string) => void
}) {
  const { nodes, edges } = useMemo(() => {
    const flow = toFlowElements(graph)
    return { nodes: applyDagreLayout(flow.nodes, flow.edges), edges: flow.edges }
  }, [graph])

  return (
    <div className="graph-canvas">
      <ReactFlowProvider>
        <ReactFlow nodes={nodes} edges={edges} fitView onNodeClick={(_, node) => onNodeClick(node.id)}>
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  )
}

type ViewMode = 'table' | 'graph'

export default function NamespaceInspect() {
  const { namespace } = useNamespaceContext()
  const [searchParams, setSearchParams] = useSearchParams()

  const [entities, setEntities] = useState<Entity[]>([])
  const [facts, setFacts] = useState<Fact[]>([])
  const [graph, setGraph] = useState<Graph | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<ViewMode | null>(null)
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)

  useEffect(() => {
    Promise.all([listEntities(namespace), listFacts(namespace), getGraph(namespace)])
      .then(([fetchedEntities, fetchedFacts, fetchedGraph]) => {
        setEntities(fetchedEntities)
        setFacts(fetchedFacts)
        setGraph(fetchedGraph)
        setMode((current) => current ?? (shouldDefaultToGraph(fetchedGraph.nodes.length) ? 'graph' : 'table'))
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : 'Failed to load entities')
      })
      .finally(() => setLoading(false))
    // Mount-only: this pane remounts on namespace change via NamespaceWorkspace's key={name}.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const focusId = searchParams.get('focus')
  const attemptedFocusRef = useRef<string | null>(null)

  useEffect(() => {
    if (!focusId) return

    function clearFocusParam() {
      setSearchParams(
        (current) => {
          const next = new URLSearchParams(current)
          next.delete('focus')
          return next
        },
        { replace: true },
      )
    }

    const match = entities.find((e) => e.entity_id === focusId)
    if (match) {
      setSelectedEntity(match)
      setQuery(match.entity_id)
      clearFocusParam()
      return
    }

    // Not in the currently loaded list - this pane may have been mounted
    // (and fetched once) before the entity was created elsewhere, e.g. a
    // cross-link from Train while Inspect was already the active view.
    // Refetch once per focus id before giving up.
    if (attemptedFocusRef.current === focusId) {
      clearFocusParam()
      return
    }

    attemptedFocusRef.current = focusId
    listEntities(namespace)
      .then(setEntities)
      .catch(() => clearFocusParam())
    // Only re-run when the focus param, the entity list, or the namespace change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId, entities, namespace])

  const factCounts = useMemo(() => countFactsByEntity(facts), [facts])
  const filtered = useMemo(() => filterEntities(entities, query), [entities, query])
  const visible = filtered.slice(0, TABLE_ROW_CAP)

  const filteredGraph = useMemo(() => {
    if (!graph) return null
    if (!query.trim()) return graph

    const ids = new Set(filtered.map((e) => e.entity_id))
    return {
      ...graph,
      nodes: graph.nodes.filter((node) => ids.has(node.id)),
      edges: graph.edges.filter((edge) => ids.has(edge.source) && ids.has(edge.target)),
    }
  }, [graph, query, filtered])

  function openEntity(entityId: string) {
    const match = entities.find((e) => e.entity_id === entityId)
    if (match) setSelectedEntity(match)
  }

  const isLargeGraph = (graph?.nodes.length ?? 0) > GRAPH_NODE_THRESHOLD

  return (
    <div className="inspect-page">
      <div className="inspect-toolbar">
        <div className="inspect-search">
          <Search size={14} />
          <input
            placeholder="Search entities, labels, surface texts…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <div className="view-toggle">
          <button
            type="button"
            className={mode === 'table' ? 'active' : ''}
            onClick={() => setMode('table')}
          >
            <LayoutGrid size={14} />
            Table
          </button>
          <button
            type="button"
            className={mode === 'graph' ? 'active' : ''}
            onClick={() => setMode('graph')}
          >
            <Share2 size={14} />
            Graph
          </button>
        </div>
      </div>

      {loading && <p>Loading&hellip;</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && entities.length === 0 && (
        <p className="muted">No entities yet - add some on the Train tab.</p>
      )}

      {!loading && !error && entities.length > 0 && mode === 'table' && (
        <>
          {filtered.length > TABLE_ROW_CAP && (
            <p className="muted small">
              Showing {TABLE_ROW_CAP} of {filtered.length} matches - refine your search to narrow
              further.
            </p>
          )}
          <table className="inspect-table">
            <thead>
              <tr>
                <th>Entity</th>
                <th>Label</th>
                <th>Surface texts</th>
                <th>Facts</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((entity) => (
                <tr
                  key={entity.entity_id}
                  className="inspect-row"
                  onClick={() => setSelectedEntity(entity)}
                >
                  <td>
                    <code>{entity.entity_id}</code>
                  </td>
                  <td>{entity.label || '—'}</td>
                  <td className="muted small">{entity.surface_texts.join(', ') || '—'}</td>
                  <td>{factCounts.get(entity.entity_id) ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {!loading && !error && entities.length > 0 && mode === 'graph' && filteredGraph && (
        <>
          {isLargeGraph && (
            <p className="muted small">
              Large graph ({graph?.nodes.length} entities) - search to narrow before relying on the
              graph view for performance.
            </p>
          )}
          <GraphCanvas graph={filteredGraph} onNodeClick={openEntity} />
        </>
      )}

      <EntityDetailPanel
        key={selectedEntity?.entity_id ?? 'inspect-panel-closed'}
        namespace={namespace}
        entity={selectedEntity}
        onOpenChange={() => setSelectedEntity(null)}
        onEntityChanged={(updated) => {
          setEntities((current) =>
            current.map((e) => (e.entity_id === updated.entity_id ? updated : e)),
          )
          setSelectedEntity(updated)
        }}
        onEntityDeleted={(entityId) => {
          setEntities((current) => current.filter((e) => e.entity_id !== entityId))
          setSelectedEntity(null)
        }}
      />
    </div>
  )
}

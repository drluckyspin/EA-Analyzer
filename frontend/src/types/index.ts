export interface Diagram {
  diagram_id: string
  title: string
  extracted_at: string
  index: number
}

export interface DiagramDetail {
  diagram_id: string
  title: string
  extracted_at: string
  node_counts: Record<string, number>
  relationship_counts: Record<string, number>
  total_nodes: number
  total_relationships: number
  metadata: Record<string, any>
}

export interface GraphData {
  nodes: ReactFlowNode[]
  edges: ReactFlowEdge[]
  metadata: Record<string, any>
}

export interface ReactFlowNode {
  id: string
  type: string
  data: {
    label: string
    type: string
    properties: Record<string, any>
  }
  position: {
    x: number
    y: number
  }
}

export interface ReactFlowEdge {
  id: string
  source: string
  target: string
  type: string
  data: {
    type: string
    properties: Record<string, any>
  }
}

export interface NodeResponse {
  id: string
  type: string
  name: string | null
  properties: Record<string, any>
}

export interface EdgeResponse {
  id: string
  from_node: string
  to_node: string
  type: string
  properties: Record<string, any>
}

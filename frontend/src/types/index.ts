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

// Upload and Analysis API Types
export interface UploadResponse {
  upload_id: string
  filename: string
  file_size: number
  file_type: string
  message: string
}

export interface AnalysisSummary {
  total_nodes: number
  total_edges: number
  has_calculations: boolean
  node_types: string[]
  edge_types: string[]
  title: string
  analyzed_at: string
}

export interface AnalysisResult {
  upload_id: string
  diagram_data: GraphData
  analysis_summary: AnalysisSummary
  success: boolean
  error?: string
}

export interface StorageResult {
  upload_id: string
  diagram_id: string
  storage_summary: Record<string, any>
  success: boolean
  error?: string
}

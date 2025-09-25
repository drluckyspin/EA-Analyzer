import { Diagram, DiagramDetail, GraphData, UploadResponse, AnalysisResult, StorageResult } from '@/types'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`)
    }

    return response.json()
  }

  // Diagram endpoints
  async getDiagrams(): Promise<Diagram[]> {
    return this.request<Diagram[]>('/api/diagrams/')
  }

  async getDiagramSummary(diagramId: string): Promise<DiagramDetail> {
    return this.request<DiagramDetail>(`/api/diagrams/${diagramId}/summary`)
  }

  async getDiagramGraph(diagramId: string): Promise<GraphData> {
    return this.request<GraphData>(`/api/diagrams/${diagramId}/graph`)
  }

  async deleteDiagram(diagramId: string): Promise<{ message: string; deleted: boolean }> {
    return this.request<{ message: string; deleted: boolean }>(`/api/diagrams/${diagramId}`, {
      method: 'DELETE',
    })
  }

  // Upload endpoints
  async uploadDiagram(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/diagrams/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Upload failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async analyzeDiagram(uploadId: string): Promise<AnalysisResult> {
    const formData = new FormData();
    formData.append('upload_id', uploadId);

    const response = await fetch(`${this.baseUrl}/api/diagrams/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Analysis failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async storeDiagram(uploadId: string, diagramData: GraphData): Promise<StorageResult> {
    const formData = new FormData();
    formData.append('upload_id', uploadId);
    formData.append('diagram_data', JSON.stringify(diagramData));

    const response = await fetch(`${this.baseUrl}/api/diagrams/store`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Storage failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health')
  }
}

export const apiClient = new ApiClient()
export default apiClient

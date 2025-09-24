import { Diagram, DiagramDetail, GraphData } from '@/types'

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

  async deleteDiagram(diagramId: string): Promise<{ message: string; deleted: any }> {
    return this.request<{ message: string; deleted: any }>(`/api/diagrams/${diagramId}`, {
      method: 'DELETE',
    })
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>('/health')
  }
}

export const apiClient = new ApiClient()
export default apiClient

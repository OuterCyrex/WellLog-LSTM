const API_BASE = '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {}),
    },
  })

  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json') ? await response.json() : await response.text()

  if (!response.ok) {
    const message = typeof payload === 'string' ? payload : payload?.detail || payload?.message || `请求失败(${response.status})`
    throw new Error(message)
  }

  return payload
}

function toQuery(params = {}) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  })
  return search.toString()
}

export const api = {
  health: () => request('/health'),
  summary: () => request('/summary'),
  wells: () => request('/wells'),
  createWell: (payload) => request('/wells', { method: 'POST', body: JSON.stringify(payload) }),
  updateWell: (id, payload) => request(`/wells/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  deleteWell: (id) => request(`/wells/${id}`, { method: 'DELETE' }),
  imports: (wellId) => request(`/wells/${wellId}/imports`),
  uploadImport: (wellId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/wells/${wellId}/imports`, { method: 'POST', body: formData })
  },
  predict: (wellId, importId) => {
    const query = toQuery({ import_id: importId })
    return request(`/wells/${wellId}/predict${query ? `?${query}` : ''}`, { method: 'POST' })
  },
  listPredictions: (wellId) => {
    const query = toQuery({ well_id: wellId })
    return request(`/predictions${query ? `?${query}` : ''}`)
  },
  prediction: (id) => request(`/predictions/${id}`),
}

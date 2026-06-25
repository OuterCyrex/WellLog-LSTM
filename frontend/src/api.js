import { getSession } from './auth'

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
    const message = typeof payload === 'string' ? payload : payload?.message || payload?.detail || `请求失败(${response.status})`
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

function normalizeUser(user) {
  if (!user) return user
  return {
    ...user,
    created_at: user.createdAt ?? user.created_at ?? null,
    updated_at: user.updatedAt ?? user.updated_at ?? null,
  }
}

function normalizeWell(well) {
  if (!well) return well
  return {
    ...well,
    import_count: well.importCount ?? well.import_count ?? 0,
    prediction_count: well.predictionCount ?? well.prediction_count ?? 0,
    last_import_at: well.lastImportAt ?? well.last_import_at ?? null,
    last_prediction_at: well.lastPredictionAt ?? well.last_prediction_at ?? null,
    created_at: well.createdAt ?? well.created_at ?? null,
    updated_at: well.updatedAt ?? well.updated_at ?? null,
  }
}

function normalizeImport(item) {
  if (!item) return item
  return {
    ...item,
    original_name: item.fileName ?? item.original_name ?? '',
    stored_path: item.fileName ?? item.stored_path ?? '',
    row_count: item.fileSize ?? item.row_count ?? 0,
    created_at: item.createdAt ?? item.created_at ?? null,
    updated_at: item.updatedAt ?? item.updated_at ?? null,
  }
}

function parseResultJson(value) {
  if (!value) return {}
  if (typeof value === 'object') return value
  try {
    return JSON.parse(value)
  } catch {
    return {}
  }
}

function normalizePrediction(item) {
  if (!item) return item
  const result = parseResultJson(item.resultJson ?? item.result_json)
  const metrics = result.metrics ?? item.metrics ?? {}
  const depth = Array.isArray(result.depth ?? item.depth) ? (result.depth ?? item.depth).map(Number) : []
  const yTrue = Array.isArray(result.y_true ?? item.y_true) ? (result.y_true ?? item.y_true).map(Number) : []
  const yPred = Array.isArray(result.y_pred ?? item.y_pred) ? (result.y_pred ?? item.y_pred).map(Number) : []
  return {
    ...item,
    well_id: item.wellId ?? item.well_id ?? null,
    well_name: item.wellName ?? item.well_name ?? result.well_name ?? '',
    import_id: item.importId ?? item.import_id ?? null,
    model_name: item.modelName ?? item.model_name ?? result.model_name ?? '',
    status: item.status ?? 'DONE',
    summary: item.summary ?? '',
    result_json: result,
    created_at: item.createdAt ?? item.created_at ?? null,
    updated_at: item.updatedAt ?? item.updated_at ?? null,
    metrics: {
      R: Number(metrics.R ?? 0),
      R2: Number(metrics.R2 ?? 0),
      MAE: Number(metrics.MAE ?? 0),
      RMSE: Number(metrics.RMSE ?? 0),
    },
    depth,
    y_true: yTrue,
    y_pred: yPred,
  }
}

function mapList(items, mapper) {
  return Array.isArray(items) ? items.map(mapper) : []
}

function currentOwnerId() {
  return getSession()?.id ?? null
}

export const api = {
  register: (payload) => request('/users', { method: 'POST', body: JSON.stringify(payload) }).then(normalizeUser),
  login: (payload) => request('/users/login', { method: 'POST', body: JSON.stringify(payload) }).then(normalizeUser),
  userById: (id) => request(`/users/${id}`).then(normalizeUser),
  users: () => request('/users').then((items) => mapList(items, normalizeUser)),
  health: () => request('/health'),
  summary: async () => {
    const [wells, predictions] = await Promise.all([api.wells(), api.listPredictions()])
    return {
      wells: wells.length,
      imports: wells.reduce((total, item) => total + Number(item.import_count || 0), 0),
      predictions: predictions.length,
      latest_prediction: predictions[0] || null,
    }
  },
  wells: () => request('/wells').then((items) => mapList(items, normalizeWell)),
  createWell: (payload) =>
    request('/wells', {
      method: 'POST',
      body: JSON.stringify({
        ...payload,
        ownerUserId: payload.ownerUserId ?? currentOwnerId(),
      }),
    }).then(normalizeWell),
  updateWell: (id, payload) => request(`/wells/${id}`, { method: 'PUT', body: JSON.stringify(payload) }).then(normalizeWell),
  deleteWell: (id) => request(`/wells/${id}`, { method: 'DELETE' }),
  imports: (wellId) => request(`/wells/${wellId}/imports`).then((items) => mapList(items, normalizeImport)),
  uploadImport: (wellId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request(`/wells/${wellId}/imports`, { method: 'POST', body: formData }).then(normalizeImport)
  },
  predict: (wellId, importId) => {
    const query = toQuery({ importId })
    return request(`/wells/${wellId}/predict${query ? `?${query}` : ''}`, { method: 'POST' }).then(normalizePrediction)
  },
  listPredictions: (wellId) => {
    const path = wellId ? `/wells/${wellId}/predictions` : '/predictions'
    return request(path).then((items) => mapList(items, normalizePrediction))
  },
  prediction: (id) => request(`/predictions/${id}`).then(normalizePrediction),
}

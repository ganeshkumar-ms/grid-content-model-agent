const API_BASE = import.meta.env.VITE_API_BASE || ''

export async function modelContent({ file, text, conversationHistory = [] }) {
  const formData = new FormData()
  if (file) {
    formData.append('file', file)
  }
  if (text) {
    formData.append('text', text)
  }
  formData.append('conversation_history', JSON.stringify(conversationHistory))

  const url = `${API_BASE}/api/model`
  const res = await fetch(url, {
    method: 'POST',
    body: formData
  })

  if (!res.ok) {
    const errText = await res.text()
    let errMsg = `Request failed (${res.status})`
    try {
      const parsed = JSON.parse(errText)
      errMsg = parsed.detail || parsed.message || errMsg
    } catch {
      errMsg = errText || errMsg
    }
    throw new Error(errMsg)
  }

  return res.json()
}

export function toViewerDoc(meta) {
  if (!meta) return null
  return {
    name: meta.filename || meta.name || 'Document',
    viewUrl: meta.view_url
      ? (meta.view_url.startsWith('http') ? meta.view_url : `${API_BASE}${meta.view_url}`)
      : null,
    downloadUrl: meta.url
      ? (meta.url.startsWith('http') ? meta.url : `${API_BASE}${meta.url}`)
      : null,
    preview: meta.preview || '',
    rawMeta: meta
  }
}


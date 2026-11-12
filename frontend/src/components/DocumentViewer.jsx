import { useState } from 'react'

export default function DocumentViewer({ doc, onClose }) {
  const [activeTab, setActiveTab] = useState('preview') // 'preview' | 'meta'

  if (!doc) return null

  const isPdf = (doc.name || '').toLowerCase().endsWith('.pdf')
  const isImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(doc.name || '')
  const hasViewUrl = Boolean(doc.viewUrl)

  return (
    <aside className="docViewer">
      <div className="docViewerHead">
        <div className="docViewerTitleWrap">
          <span className="docViewerIcon">📄</span>
          <span className="docViewerTitle" title={doc.name}>{doc.name}</span>
        </div>
        <div className="docViewerActions">
          {doc.downloadUrl && (
            <a
              href={doc.downloadUrl}
              download={doc.name}
              className="docViewerBtn"
              title="Download file"
            >
              <svg className="icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
            </a>
          )}
          <button
            onClick={onClose}
            className="docViewerCloseBtn"
            title="Close viewer"
            type="button"
          >
            ✕
          </button>
        </div>
      </div>

      <div className="docViewerTabs">
        <button
          className={`docTab${activeTab === 'preview' ? ' active' : ''}`}
          onClick={() => setActiveTab('preview')}
          type="button"
        >
          Viewer
        </button>
        <button
          className={`docTab${activeTab === 'meta' ? ' active' : ''}`}
          onClick={() => setActiveTab('meta')}
          type="button"
        >
          Extracted Content
        </button>
      </div>

      <div className="docViewerBody">
        {activeTab === 'preview' ? (
          hasViewUrl ? (
            isImage ? (
              <div className="docViewerImage">
                <img src={doc.viewUrl} alt={doc.name} />
              </div>
            ) : (
              <iframe
                src={doc.viewUrl}
                title={doc.name}
                className="docViewerIframe"
              />
            )
          ) : (
            <div className="docViewerFallback">
              <pre className="docViewerText">{doc.preview || 'No preview available.'}</pre>
            </div>
          )
        ) : (
          <div className="docViewerMeta">
            <div className="metaRow">
              <span className="metaKey">Filename</span>
              <span className="metaVal">{doc.name}</span>
            </div>
            {doc.rawMeta?.size && (
              <div className="metaRow">
                <span className="metaKey">Size</span>
                <span className="metaVal">{(doc.rawMeta.size / 1024).toFixed(1)} KB</span>
              </div>
            )}
            {doc.rawMeta?.words && (
              <div className="metaRow">
                <span className="metaKey">Word Count</span>
                <span className="metaVal">{doc.rawMeta.words} words</span>
              </div>
            )}
            {doc.rawMeta?.content_type && (
              <div className="metaRow">
                <span className="metaKey">Type</span>
                <span className="metaVal">{doc.rawMeta.content_type}</span>
              </div>
            )}
            <div className="metaSection">
              <div className="metaSectionTitle">Extracted Content Preview</div>
              <pre className="docViewerText">{doc.preview || 'No text extracted.'}</pre>
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}


import { useState } from 'react'

export default function GridResultCard({ data, result, onOpenDoc }) {
  const [copiedPayload, setCopiedPayload] = useState(false)
  const [activeTab, setActiveTab] = useState('components') // 'components' | 'schema' | 'recommendations'

  const activeData = data || result
  if (!activeData) return null

  // Fallback to plain conversational response if chat
  if (activeData.type === 'chat' || (!activeData.model_readiness && activeData.message)) {
    return (
      <div className="gridChatReply">
        <p>{activeData.message}</p>
      </div>
    )
  }

  const mr = activeData.model_readiness || {}
  const metrics = activeData.metrics || {}
  const contentTypes = Array.isArray(activeData.content_types) ? activeData.content_types : []
  const schemaPayload = activeData.schema_payload || {}
  const recommendations = Array.isArray(activeData.recommendations) ? activeData.recommendations : []

  const score = typeof mr.score === 'number' ? mr.score : 85
  const status = mr.status || (score >= 85 ? 'OPTIMAL_GRAPH' : score < 50 ? 'MONOLITHIC_DETECTED' : 'COMPONENTS_DEFINED')

  const statusConfig = {
    OPTIMAL_GRAPH: {
      label: 'OPTIMAL COMPONENT GRAPH',
      icon: '✓',
      badgeClass: 'statusOptimal',
      color: '#b7ff00'
    },
    COMPONENTS_DEFINED: {
      label: 'COMPONENTS DEFINED',
      icon: '⚡',
      badgeClass: 'statusWarn',
      color: '#d4ff66'
    },
    MONOLITHIC_DETECTED: {
      label: 'MONOLITHIC DETECTED',
      icon: '⛔',
      badgeClass: 'statusDanger',
      color: '#ff5c5c'
    }
  }[status] || {
    label: 'MODEL ARCHITECTED',
    icon: 'ℹ',
    badgeClass: 'statusOptimal',
    color: '#b7ff00'
  }

  function handleCopyPayload() {
    const text = JSON.stringify(schemaPayload, null, 2)
    navigator.clipboard.writeText(text).then(() => {
      setCopiedPayload(true)
      setTimeout(() => setCopiedPayload(false), 2000)
    })
  }

  return (
    <div className="gridResultCard">
      {/* Header: Architecture Score & Assessment */}
      <div className="gridScoreHeader">
        <div className="gridScoreBadgeWrap">
          <span className={`gridStatusBadge ${statusConfig.badgeClass}`}>
            <span className="badgeDot" />
            {statusConfig.icon} {statusConfig.label}
          </span>
          <div className="gridScoreNumberWrap">
            <span className="gridScoreNumber" style={{ color: statusConfig.color }}>{score}</span>
            <span className="gridScoreMax">/ 100</span>
          </div>
        </div>

        <div className="gridScoreBarBg">
          <div
            className="gridScoreBarFill"
            style={{
              width: `${Math.min(100, Math.max(0, score))}%`,
              backgroundColor: statusConfig.color
            }}
          />
        </div>

        {mr.summary && (
          <p className="gridSummaryText">{mr.summary}</p>
        )}
      </div>

      {/* Sleek Findings Ribbon (Zero bulky boxes!) */}
      <div className="gridMetricsStrip">
        <div className="gridMetricPill">
          <div className="gridMetricLeft">
            <span className="metricDot types" />
            <span className="metricLabel">Content Types</span>
          </div>
          <b className="metricCount types">
            {metrics.content_types_count || contentTypes.length || 0}
          </b>
        </div>

        <div className="gridMetricPill">
          <div className="gridMetricLeft">
            <span className="metricDot comp" />
            <span className="metricLabel">Atomic Components</span>
          </div>
          <b className="metricCount comp">
            {metrics.atomic_components_count || 0}
          </b>
        </div>

        <div className="gridMetricPill">
          <div className="gridMetricLeft">
            <span className="metricDot links" />
            <span className="metricLabel">Relations</span>
          </div>
          <b className="metricCount links">
            {metrics.relational_links_count || 0}
          </b>
        </div>

        <div className="gridMetricPill full">
          <div className="gridMetricLeft">
            <span className="metricDot tier" />
            <span className="metricLabel">Reusability</span>
          </div>
          <span className="metricTierText">
            {metrics.reusability_tier || 'Atomic Design'}
          </span>
        </div>
      </div>

      {/* Workspace Tabs */}
      <div className="gridCardTabs">
        <button
          type="button"
          className={`gridTabBtn${activeTab === 'components' ? ' on' : ''}`}
          onClick={() => setActiveTab('components')}
        >
          Component Graph ({contentTypes.length})
        </button>
        <button
          type="button"
          className={`gridTabBtn${activeTab === 'schema' ? ' on' : ''}`}
          onClick={() => setActiveTab('schema')}
        >
          JSON Schema
        </button>
        <button
          type="button"
          className={`gridTabBtn${activeTab === 'recommendations' ? ' on' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          Architecture ({recommendations.length})
        </button>
      </div>

      {/* TAB 1: Content Types & Component Graph */}
      {activeTab === 'components' && (
        <div className="gridComponentsWrap">
          {contentTypes.length > 0 ? (
            contentTypes.map((ct, idx) => (
              <div key={idx} className="gridTypeCard">
                <div className="gridTypeHead">
                  <div className="gridTypeHeadLeft">
                    <span className="typeKindBadge">{ct.type_kind || 'Content Model'}</span>
                    <b className="typeName">{ct.name}</b>
                  </div>
                  {Array.isArray(ct.references) && ct.references.length > 0 && (
                    <div className="typeRefPill">
                      <span>Links &rarr; </span>
                      {ct.references.join(', ')}
                    </div>
                  )}
                </div>

                {ct.description && (
                  <p className="typeDesc">{ct.description}</p>
                )}

                {Array.isArray(ct.fields) && ct.fields.length > 0 && (
                  <div className="gridFieldsTableWrap">
                    <table className="gridFieldsTable">
                      <thead>
                        <tr>
                          <th>Field Label</th>
                          <th>API Key</th>
                          <th>Data Type</th>
                          <th>Constraints</th>
                          <th>Flags</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ct.fields.map((f, fIdx) => (
                          <tr key={fIdx}>
                            <td className="fieldLabelCell"><b>{f.name}</b></td>
                            <td className="fieldKeyCell"><code>{f.api_key}</code></td>
                            <td className="fieldTypeCell">
                              <span className="fieldTypeTag">{f.type}</span>
                            </td>
                            <td className="fieldValidationCell">{f.validation || 'Standard'}</td>
                            <td className="fieldFlagsCell">
                              {f.required && <span className="flagTag req">Required</span>}
                              {f.localized && <span className="flagTag loc">i18n</span>}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="gridEmptyTab">No content types generated.</div>
          )}
        </div>
      )}

      {/* TAB 2: JSON Schema Payload */}
      {activeTab === 'schema' && (
        <div className="gridPayloadWrap">
          <div className="gridPayloadHead">
            <span className="payloadNote">Headless CMS compliant JSON Schema ready for automated CLI ingestion.</span>
            <button
              type="button"
              className="copyPayloadBtn"
              onClick={handleCopyPayload}
            >
              {copiedPayload ? '✓ Copied!' : 'Copy Schema'}
            </button>
          </div>
          <pre className="gridPayloadPre">
            <code>{JSON.stringify(schemaPayload, null, 2)}</code>
          </pre>
        </div>
      )}

      {/* TAB 3: Architecture Recommendations */}
      {activeTab === 'recommendations' && (
        <div className="gridRecsWrap">
          {recommendations.length > 0 ? (
            recommendations.map((rec, idx) => (
              <div key={idx} className="gridRecItem">
                <span className="recNumber">{idx + 1}</span>
                <p className="recText">{rec}</p>
              </div>
            ))
          ) : (
            <div className="gridEmptyTab">All components conform to atomic design guidelines.</div>
          )}
        </div>
      )}
    </div>
  )
}

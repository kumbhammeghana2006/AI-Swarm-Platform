/**
 * MetricsDashboard component renders empirical evaluation metrics
 * captured across swarm task executions.
 */
export default function MetricsDashboard({ metrics, isLoading, onRefresh }) {
  if (!metrics) {
    return (
      <div className="metrics-card">
        <div className="metrics-header">
          <div>
            <h2 className="card-title">Evaluation & Research Metrics</h2>
            <p className="metrics-subtitle">Empirical performance benchmarks across multi-agent swarm tasks.</p>
          </div>
        </div>
        <p className="history-empty">
          {isLoading ? 'Calculating evaluation metrics...' : 'No evaluation metrics recorded yet. Submit a swarm task to view measurable data.'}
        </p>
      </div>
    )
  }

  const agentEntries = Object.entries(metrics.agent_usage_frequency || {})
  const totalAgentRuns = agentEntries.reduce((acc, [, count]) => acc + count, 0)
  const taskTypeEntries = Object.entries(metrics.task_type_distribution || {})
  const configEntries = Object.entries(metrics.configuration_distribution || {})

  return (
    <div className="metrics-card">
      <div className="metrics-header">
        <div>
          <div className="metrics-title-row">
            <h2 className="card-title">Evaluation & Research Metrics</h2>
            <span className="scope-badge">Scope: {metrics.scope || 'user'}</span>
          </div>
          <p className="metrics-subtitle">
            Empirical measurements assessing dynamic orchestration, Okapi BM25 retrieval, and iterative self-correction.
          </p>
        </div>
        {onRefresh && (
          <button
            type="button"
            className="refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh metrics summary"
          >
            {isLoading ? 'Updating...' : 'Refresh Metrics'}
          </button>
        )}
      </div>

      {/* Top Stat Summary Grid */}
      <div className="metrics-kpi-grid">
        <div className="kpi-card">
          <span className="kpi-label">Total Tasks</span>
          <span className="kpi-value">{metrics.total_tasks}</span>
          <span className="kpi-subtext">
            {metrics.successful_tasks} completed · {metrics.failed_tasks} failed
          </span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Success Rate</span>
          <span className="kpi-value highlight-accent">{metrics.success_rate}%</span>
          <div className="kpi-progress-bar">
            <div
              className="kpi-progress-fill success-fill"
              style={{ width: `${Math.min(metrics.success_rate, 100)}%` }}
            />
          </div>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Avg Execution Time</span>
          <span className="kpi-value">{metrics.avg_execution_time_seconds.toFixed(2)}s</span>
          <span className="kpi-subtext">Wall-clock inference latency</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Avg Iterations</span>
          <span className="kpi-value">{metrics.avg_iteration_count.toFixed(1)}</span>
          <span className="kpi-subtext">Tester → Coder refinement</span>
        </div>

        <div className="kpi-card">
          <span className="kpi-label">Tester PASS Rate</span>
          <span className="kpi-value">{metrics.tester_pass_rate}%</span>
          <span className="kpi-subtext">
            {metrics.tester_pass_count} passed · {metrics.tester_fail_count} failed
          </span>
        </div>
      </div>

      {/* Distributions Row */}
      <div className="metrics-distributions-grid">
        {/* Panel 1: Agent Usage Frequency */}
        <div className="dist-panel">
          <h3 className="dist-title">Active Agent Utilization</h3>
          {agentEntries.length === 0 ? (
            <p className="dist-empty">No agent activity recorded yet.</p>
          ) : (
            <div className="agent-bars-list">
              {agentEntries
                .sort((a, b) => b[1] - a[1])
                .map(([agent, count]) => {
                  const pct = totalAgentRuns > 0 ? Math.round((count / totalAgentRuns) * 100) : 0
                  return (
                    <div key={agent} className="agent-bar-row">
                      <div className="agent-bar-header">
                        <span className="agent-name">{agent}</span>
                        <span className="agent-count">
                          {count} run{count !== 1 ? 's' : ''} ({pct}%)
                        </span>
                      </div>
                      <div className="agent-bar-track">
                        <div
                          className="agent-bar-fill"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
            </div>
          )}
        </div>

        {/* Panel 2: Task Types & Ablation Configuration */}
        <div className="dist-panel">
          <h3 className="dist-title">Task Classification & Configurations</h3>

          <div className="sub-panel-section">
            <span className="sub-panel-label">Task Type Distribution:</span>
            {taskTypeEntries.length === 0 ? (
              <p className="dist-empty">No classified tasks yet.</p>
            ) : (
              <div className="badge-wrap">
                {taskTypeEntries.map(([tType, count]) => (
                  <span key={tType} className="metric-chip">
                    <strong>{tType}</strong>: {count}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="sub-panel-section" style={{ marginTop: '16px' }}>
            <span className="sub-panel-label">Configuration & Ablation Status:</span>
            <div className="config-list">
              <div className="config-row active-config">
                <div className="config-info">
                  <span className="config-name">Multi-Agent Swarm (Full)</span>
                  <span className="config-desc">Orchestration + BM25 RAG + Self-Correction</span>
                </div>
                <span className="config-badge badge-active">
                  Active ({configEntries.find(([k]) => k === 'multi_agent')?.[1] || metrics.total_tasks})
                </span>
              </div>

              <div className="config-row planned-config">
                <div className="config-info">
                  <span className="config-name">Single-Agent Baseline</span>
                  <span className="config-desc">Reserved for controlled ablation benchmarking</span>
                </div>
                <span className="config-badge badge-planned">Benchmark Planned</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

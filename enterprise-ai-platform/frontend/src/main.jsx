import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Atom, BadgeCheck,
  BarChart3, Bell, Blocks, Bot, BrainCircuit, Check, ChevronDown, ChevronRight,
  CircleHelp, CirclePlay, Clock3, Cpu, FlaskConical, GitBranch, GitCompareArrows,
  Gauge, HardDrive, Layers3, LoaderCircle, LockKeyhole, Menu, Network, Play,
  Radio, RefreshCw, Search, Settings2, ShieldCheck, Sparkles, Workflow, Zap,
} from 'lucide-react';
import './styles.css';

const API_KEY = import.meta.env.VITE_API_KEY || 'demo-key';
const api = async (path, init = {}) => {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', 'X-API-Key': API_KEY, ...init.headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.error || `Request failed (${response.status})`);
  return data;
};

const TRACKS = [
  { id: 'jev', name: 'Jev · no-LLM work', short: 'Route structured work before it reaches a model.', icon: Zap, tint: 'violet', chip: '0 model calls', group: 'Efficiency' },
  { id: 'slm', name: 'SLM vs LLM', short: 'Explore small-model quality and cost trade-offs.', icon: BrainCircuit, tint: 'blue', chip: 'Model routing', group: 'Efficiency' },
  { id: 'edge', name: 'Edge AI', short: 'Place privacy-sensitive work on local devices.', icon: HardDrive, tint: 'teal', chip: 'Local inference', group: 'Deployment' },
  { id: 'switching', name: 'Automatic switching', short: 'Route or escalate based on confidence and task.', icon: GitCompareArrows, tint: 'amber', chip: 'Adaptive routing', group: 'Reliability' },
  { id: 'parallel', name: 'Task parallelism', short: 'Compare sequential work with concurrent DAG execution.', icon: Workflow, tint: 'blue', chip: 'DAG scheduler', group: 'Orchestration' },
  { id: 'orchestration', name: 'Orchestration agent', short: 'Simulate hierarchical, pipeline and swarm patterns.', icon: Network, tint: 'violet', chip: 'Multi-agent', group: 'Orchestration' },
  { id: 'quantization', name: 'Quantization', short: 'Inspect precision labels, quality deltas and cost.', icon: Cpu, tint: 'teal', chip: 'FP8 · INT4 · FP16', group: 'Efficiency' },
];

const DEFAULT_PROMPTS = {
  jev: 'I was charged twice for my subscription. Please refund.',
  slm: 'Classify this customer note: the delivery was excellent.',
  edge: 'Classify this private customer message without sending it to the cloud.',
  switching: 'Compare the risk and recommend the safest option.',
  parallel: 'Prepare a short launch-readiness summary from research, risk, and cost checks.',
  orchestration: 'Research the request, check risk, and prepare a combined answer.',
  quantization: 'Classify this review: the service was excellent.',
};

const fmtCurrency = (value = 0) => `$${Number(value || 0).toFixed(4)}`;
const fmtMs = (value = 0) => `${Math.round(Number(value || 0))} ms`;

function IconMark({ icon: Icon, tint = 'blue', size = 18 }) {
  return <span className={`icon-mark ${tint}`}><Icon size={size} strokeWidth={1.8} /></span>;
}

function App() {
  const [page, setPage] = useState('overview');
  const [track, setTrack] = useState('jev');
  const [models, setModels] = useState([]);
  const [runtime, setRuntime] = useState(null);
  const [suites, setSuites] = useState([]);
  const [runs, setRuns] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [online, setOnline] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [prompt, setPrompt] = useState(DEFAULT_PROMPTS.jev);
  const [category, setCategory] = useState('classification');
  const [confidence, setConfidence] = useState(0.42);
  const [selectedModel, setSelectedModel] = useState('mock-small-fp8');
  const [precision, setPrecision] = useState('fp8');
  const [privacy, setPrivacy] = useState('strict');
  const [pattern, setPattern] = useState('hierarchical');
  const [suiteId, setSuiteId] = useState('customer_support');
  const [agentVersion, setAgentVersion] = useState('demo-v1');
  const [mobileMenu, setMobileMenu] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [health, modelData, runtimeData, metricData, suiteData, runData] = await Promise.all([
        api('/health'), api('/v1/models'), api('/v1/runtime'), api('/v1/metrics/summary'),
        api('/v1/agent-eval/suites'), api('/v1/agent-eval/runs'),
      ]);
      setOnline(health.status === 'ok');
      setModels(modelData);
      setRuntime(runtimeData);
      setMetrics(metricData);
      setSuites(suiteData);
      setRuns(runData);
      const providerModels = modelData.filter((model) => model.provider === runtimeData.model_provider);
      if (providerModels.length && !providerModels.some((m) => m.id === selectedModel)) setSelectedModel(providerModels[0].id);
      if (suiteData.length && !suiteData.some((s) => s.id === suiteId)) setSuiteId(suiteData[0].id);
      setError('');
    } catch (err) {
      setOnline(false);
      setError(err.message);
    }
  }, [selectedModel, suiteId]);

  useEffect(() => { refresh(); const timer = setInterval(refresh, 12000); return () => clearInterval(timer); }, [refresh]);

  const activeTrack = TRACKS.find((item) => item.id === track) || TRACKS[0];
  const availableModels = models.filter((model) => !runtime || model.provider === runtime.model_provider);
  const activeModel = availableModels.find((item) => item.id === selectedModel) || availableModels[0];
  const chartData = useMemo(() => {
    const recent = [...runs].slice(-8);
    return recent.map((run, index) => ({
      name: `Run ${index + 1}`,
      success: Math.round((run.summary?.success_rate || 0) * 100),
      cost: Number(run.summary?.cost_usd || 0),
    }));
  }, [runs]);

  const begin = (view, chosenTrack = track) => {
    setPage(view);
    setTrack(chosenTrack);
    setResult(null);
    setError('');
    if (chosenTrack in DEFAULT_PROMPTS) setPrompt(DEFAULT_PROMPTS[chosenTrack]);
    setMobileMenu(false);
  };

  const simulate = async () => {
    setLoading(true);
    setError('');
    setResult(null);
    try {
      let data;
      if (track === 'agent-eval') {
        data = await api('/v1/agent-eval/run', { method: 'POST', body: JSON.stringify({ suite_id: suiteId, agent_version: agentVersion }) });
        setRuns((old) => [...old, data]);
        setResult({ kind: 'eval', data });
      } else {
        const body = buildRequest(track, { prompt, category, confidence, selectedModel, precision, privacy, pattern, models });
        data = await api('/v1/request', { method: 'POST', body: JSON.stringify(body) });
        setResult({ kind: 'request', data });
        refresh();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const simulateComparison = async () => {
    setLoading(true); setError(''); setResult(null);
    try {
      const examples = [
        { label: 'High confidence', confidence: 0.91 },
        { label: 'Low confidence', confidence: 0.38 },
      ];
      const rows = await Promise.all(examples.map(async (example) => {
        const data = await api('/v1/request', { method: 'POST', body: JSON.stringify({
          input: prompt, task_category: category, strategy: 'confidence_based',
          metadata: { confidence: example.confidence },
        }) });
        const routeEvent = data.trace?.events?.find((event) => event.routes)?.routes;
        return { ...example, result: data, route: routeEvent?.main || routeEvent?.[Object.keys(routeEvent || {})[0]] };
      }));
      setResult({ kind: 'comparison', rows }); refresh();
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const selectedSuite = suites.find((item) => item.id === suiteId);
  const navTo = (view, chosenTrack) => begin(view, chosenTrack);

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileMenu ? 'open' : ''}`}>
        <div className="brand-row"><div className="brand-logo"><Atom size={22} /></div><div><b>AGENTEVAL</b><small>ENTERPRISE AI LAB</small></div><button className="icon-button mobile-close" onClick={() => setMobileMenu(false)}><Menu size={18} /></button></div>
        <div className="workspace-switch"><span className="workspace-dot">R</span><span><b>Research workspace</b><small>Local environment</small></span><ChevronDown size={15} /></div>
        <div className="side-label">WORKSPACE</div>
        <button className={`nav-item ${page === 'overview' ? 'active' : ''}`} onClick={() => navTo('overview')}><BarChart3 size={17} /> Overview</button>
        <button className={`nav-item ${page === 'agent-eval' ? 'active' : ''}`} onClick={() => navTo('agent-eval', 'agent-eval')}><FlaskConical size={17} /> Agent evaluation <span className="nav-count">3</span></button>
        <div className="side-label side-label-gap">RESEARCH TRACKS</div>
        {TRACKS.map((item) => <button key={item.id} className={`nav-item ${page === 'track' && track === item.id ? 'active' : ''}`} onClick={() => navTo('track', item.id)}><item.icon size={17} /> <span>{item.name}</span></button>)}
        <div className="sidebar-spacer" />
        <div className="sidebar-status"><span className={`status-dot ${online ? 'online' : ''}`} /><span>{online ? 'API connected' : 'API disconnected'}</span><button title="Refresh connection" onClick={refresh}><RefreshCw size={14} /></button></div>
        <div className="sidebar-footer"><span className="avatar">NG</span><span><b>Demo operator</b><small>Local session</small></span><Settings2 size={16} /></div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <button className="icon-button mobile-menu" onClick={() => setMobileMenu(true)}><Menu size={20} /></button>
          <div className="breadcrumbs"><span>Workspace</span><ChevronRight size={14} /><b>{page === 'overview' ? 'Overview' : page === 'agent-eval' ? 'Agent evaluation' : activeTrack.name}</b></div>
          <div className="topbar-actions"><div className={`connection-pill ${online ? 'connected' : 'disconnected'}`}><span className="status-dot" />{online ? 'Backend live' : 'Backend offline'}</div><button className="icon-button" title="Refresh data" onClick={refresh}><RefreshCw size={16} /></button><button className="icon-button" title="Help"><CircleHelp size={17} /></button><button className="icon-button" title="Notifications"><Bell size={17} /><i /></button></div>
        </header>

        {error && <div className="global-error"><Radio size={16} /><span>{online ? error : 'Backend is offline. Start FastAPI on port 8000 to run live simulations.'}</span><button onClick={() => setError('')}>Dismiss</button></div>}

        {page === 'overview' && <Overview metrics={metrics} chartData={chartData} runs={runs} online={online} onSelect={navTo} />}
        {page === 'track' && <TrackView track={activeTrack} prompt={prompt} setPrompt={setPrompt} category={category} setCategory={setCategory} confidence={confidence} setConfidence={setConfidence} models={availableModels} selectedModel={selectedModel} setSelectedModel={setSelectedModel} activeModel={activeModel} precision={precision} setPrecision={setPrecision} privacy={privacy} setPrivacy={setPrivacy} pattern={pattern} setPattern={setPattern} loading={loading} online={online} result={result} error={error} onRun={simulate} onCompare={simulateComparison} runtime={runtime} />}
        {page === 'agent-eval' && <EvalView suites={suites} suiteId={suiteId} setSuiteId={setSuiteId} selectedSuite={selectedSuite} agentVersion={agentVersion} setAgentVersion={setAgentVersion} runs={runs} loading={loading} result={result} error={error} onRun={simulate} />}
        <footer className="page-footer"><span>AGENTEVAL ENTERPRISE <i>·</i> LOCAL DEMO</span><span>Mock mode is clearly labeled · No external model calls by default</span></footer>
      </main>
      {mobileMenu && <button className="scrim" aria-label="Close menu" onClick={() => setMobileMenu(false)} />}
    </div>
  );
}

function Overview({ metrics, chartData, runs, online, onSelect }) {
  const requests = metrics?.request_count ?? 0;
  const cost = metrics?.cost_usd ?? 0;
  const savings = metrics?.savings_pct ?? 0;
  return <div className="content-page">
    <section className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> AI SYSTEMS CONTROL ROOM</div><h1>Evaluate. Route. Improve.</h1><p>Simulate agent quality, model efficiency, and deployment strategies in one workspace.</p></div><button className="button button-primary" onClick={() => onSelect('agent-eval', 'agent-eval')}><CirclePlay size={17} /> Run an evaluation <ArrowRight size={16} /></button></section>
    <div className="notice-banner"><span className="notice-icon"><Sparkles size={17} /></span><div><b>Demo environment ready</b><p>{online ? 'Connected to the local API. Simulations will create real traces and persist evaluation runs.' : 'Start the FastAPI backend to connect live simulations. The default adapters use mock models and need no keys.'}</p></div><span className={`notice-state ${online ? 'live' : ''}`}><i />{online ? 'LIVE' : 'LOCAL'}</span></div>
    <div className="metric-grid">
      <MetricCard icon={Activity} tint="blue" label="Requests evaluated" value={requests.toLocaleString()} delta="Across all task types" trend="neutral" />
      <MetricCard icon={Gauge} tint="violet" label="Estimated spend" value={fmtCurrency(cost)} delta="From local request history" trend="neutral" />
      <MetricCard icon={ArrowDownRight} tint="teal" label="Cost savings" value={`${Number(savings).toFixed(1)}%`} delta="Estimate vs advanced baseline" trend="positive" />
      <MetricCard icon={BadgeCheck} tint="amber" label="Evaluation suites" value="03" delta="Ready to run locally" trend="neutral" />
    </div>
    <div className="section-heading"><div><div className="eyebrow">SIMULATION WORKBENCH</div><h2>Choose a research track</h2><p>Each module is interactive and leaves an inspectable trace.</p></div><span className="section-extra"><span className="status-dot online" /> 7 tracks available</span></div>
    <div className="track-grid">{TRACKS.map((item, index) => <button key={item.id} className="track-card" onClick={() => onSelect('track', item.id)}><div className="track-card-top"><IconMark icon={item.icon} tint={item.tint} /><span className="track-index">0{index + 1}</span></div><h3>{item.name}</h3><p>{item.short}</p><div className="track-card-foot"><span className="track-chip">{item.chip}</span><span className="round-arrow"><ArrowRight size={15} /></span></div></button>)}</div>
    <div className="lower-grid"><section className="panel chart-panel"><div className="panel-heading"><div><h3>Evaluation trend</h3><p>Success rate across recent evaluation runs</p></div><span className="select-pill">Recent runs <ChevronDown size={13} /></span></div>{chartData.length ? <div className="chart-wrap"><SuccessChart data={chartData} /></div> : <div className="empty-chart"><BarChart3 size={22} /><span>Run an evaluation to populate this chart.</span></div>}</section>
      <section className="panel recent-panel"><div className="panel-heading"><div><h3>Recent evaluation runs</h3><p>Latest suite activity</p></div><button className="text-button" onClick={() => onSelect('agent-eval', 'agent-eval')}>View all <ArrowRight size={14} /></button></div>{runs.length ? <div className="recent-list">{[...runs].slice(-4).reverse().map((run) => <div className="recent-row" key={run.run_id}><span className={`run-status ${run.summary?.failed ? 'warn' : ''}`}><Check size={13} /></span><div className="recent-main"><b>{run.suite}</b><small>{run.agent_version} · {new Date(run.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small></div><div className="recent-score"><b>{Math.round((run.summary?.success_rate || 0) * 100)}%</b><small>success</small></div></div>)}</div> : <div className="empty-recent"><span className="empty-icon"><FlaskConical size={18} /></span><b>No runs yet</b><span>Start an evaluation to see release history here.</span><button className="text-button" onClick={() => onSelect('agent-eval', 'agent-eval')}>Open eval studio <ArrowRight size={14} /></button></div>}</section></div>
  </div>;
}

function MetricCard({ icon, tint, label, value, delta, trend }) {
  const Icon = icon;
  return <div className="metric-card"><div className="metric-card-head"><IconMark icon={Icon} tint={tint} /><span className="metric-menu">···</span></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className={`metric-delta ${trend}`}>{trend === 'positive' ? <ArrowDownRight size={14} /> : <span className="delta-dot" />}{delta}</div></div>;
}

function SuccessChart({ data }) {
  const width = 620, height = 178, left = 34, right = 10, top = 10, bottom = 26;
  const xAt = (index) => left + index * ((width - left - right) / Math.max(1, data.length - 1));
  const yAt = (value) => top + (100 - value) * ((height - top - bottom) / 100);
  const line = data.map((point, index) => `${index ? 'L' : 'M'} ${xAt(index)} ${yAt(point.success)}`).join(' ');
  const area = `${line} L ${xAt(data.length - 1)} ${height - bottom} L ${xAt(0)} ${height - bottom} Z`;
  return <svg className="success-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Evaluation success rate trend">
    {[0, 25, 50, 75, 100].map((value) => <g key={value}><line x1={left} x2={width - right} y1={yAt(value)} y2={yAt(value)} stroke="#eef1f6" /><text x={left - 8} y={yAt(value) + 3} textAnchor="end" fill="#9aa4b2" fontSize="9">{value}</text></g>)}
    <path d={area} fill="url(#success-fill)" /><defs><linearGradient id="success-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#5879ef" stopOpacity=".22" /><stop offset="100%" stopColor="#5879ef" stopOpacity="0" /></linearGradient></defs>
    <path d={line} fill="none" stroke="#5879ef" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    {data.map((point, index) => <g key={point.name}><circle cx={xAt(index)} cy={yAt(point.success)} r="4" fill="#fff" stroke="#5879ef" strokeWidth="2"><title>{`${point.name}: ${point.success}%`}</title></circle><text x={xAt(index)} y={height - 7} textAnchor="middle" fill="#8b95a7" fontSize="9">{point.name}</text></g>)}
  </svg>;
}

function TrackView(props) {
  const { track, prompt, setPrompt, category, setCategory, confidence, setConfidence, models, selectedModel, setSelectedModel, activeModel, precision, setPrecision, privacy, setPrivacy, pattern, setPattern, loading, online, result, error, onRun, onCompare, runtime } = props;
  const active = track.id;
  const runLabel = active === 'parallel' ? 'Run parallel DAG' : active === 'orchestration' ? 'Run orchestration plan' : active === 'switching' ? 'Simulate model routing' : 'Run simulation';
  return <div className="content-page track-page">
    <div className="track-hero"><div><div className="eyebrow"><span className="eyebrow-line" /> {track.group.toUpperCase()} · SIMULATION</div><h1>{track.name}</h1><p>{track.short} Configure a scenario and inspect the backend trace.</p></div><IconMark icon={track.icon} tint={track.tint} size={25} /></div>
    <div className="track-layout"><section className="panel config-panel"><div className="panel-heading"><div><h3>Scenario configuration</h3><p>Mock-first · Safe to run locally</p></div><span className="mock-badge"><span className="status-dot online" /> MOCK MODE</span></div>
      {active === 'jev' && <><Field label="User request"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><div className="info-callout"><Zap size={15} /><span>Structured classification runs before model routing. A Jev match can return a deterministic billing rule with zero model calls.</span></div></>}
      {active === 'slm' && <><Field label="Task category"><select value={category} onChange={(e) => setCategory(e.target.value)}><option value="classification">Classification</option><option value="extraction">Extraction</option><option value="reasoning">Reasoning</option><option value="generation">Generation</option></select></Field><Field label="Prompt"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><Field label="Model candidate"><ModelPicker models={models} selectedModel={selectedModel} onChange={setSelectedModel} /></Field><div className="model-mini-stats"><span><small>Backend provider</small><b>{runtime?.model_provider || '—'}</b></span><span><small>Catalog quality</small><b>{activeModel ? `${(activeModel.quality * 100).toFixed(1)}%` : '—'}</b></span><span><small>Input cost / 1K</small><b>{fmtCurrency(activeModel?.cost_per_1k_in)}</b></span></div></>}
      {active === 'edge' && <><Field label="Privacy policy"><select value={privacy} onChange={(e) => setPrivacy(e.target.value)}><option value="strict">Strict · keep supported tasks local</option><option value="standard">Standard · cloud allowed</option></select></Field><Field label="Task category"><select value={category} onChange={(e) => setCategory(e.target.value)}><option value="classification">Classification</option><option value="extraction">Extraction</option><option value="reasoning">Reasoning</option><option value="generation">Generation</option></select></Field><Field label="Private input"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><div className="info-callout teal-callout"><LockKeyhole size={15} /><span>Strict privacy sends classification/extraction to the configured local adapter. Unsupported task categories require cloud capability.</span></div></>}
      {active === 'switching' && <><Field label="Request to route"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><Field label="Task category"><select value={category} onChange={(e) => setCategory(e.target.value)}><option value="classification">Classification</option><option value="extraction">Extraction</option><option value="reasoning">Reasoning</option><option value="generation">Generation</option><option value="safety_critical">Safety critical</option></select></Field><label className="field-label confidence-label">Router confidence <b>{Math.round(confidence * 100)}%</b></label><input className="range-input" type="range" min="0.1" max="1" step="0.05" value={confidence} onChange={(e) => setConfidence(Number(e.target.value))} /><div className="range-hints"><span>Escalate to stronger model</span><span>Optimize for cost</span></div></>}
      {active === 'parallel' && <><Field label="DAG task"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><div className="dag-preview"><div className="dag-node parent"><span>01</span>Research</div><div className="dag-branches"><div className="dag-line" /><div className="dag-node">02 · Risk check</div><div className="dag-node">03 · Cost analysis</div></div><div className="dag-node final"><span>04</span>Synthesis</div></div><div className="info-callout"><GitBranch size={15} /><span>Independent workers run concurrently; synthesis waits for their outputs.</span></div></>}
      {active === 'orchestration' && <><Field label="Delegation pattern"><select value={pattern} onChange={(e) => setPattern(e.target.value)}><option value="hierarchical">Hierarchical · planner delegates to workers</option><option value="pipeline">Pipeline · sequential hand-offs</option><option value="swarm">Swarm · peer workers + coordinator</option></select></Field><Field label="Orchestrator task"><textarea rows="4" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><div className="pattern-tags"><span><Network size={13} /> Planner</span><span><Blocks size={13} /> Workers</span><span><GitBranch size={13} /> DAG trace</span></div><div className="info-callout amber-callout"><CircleHelp size={15} /><span>The demo planner is deterministic; connect a planning agent adapter for autonomous decomposition.</span></div></>}
      {active === 'quantization' && <><Field label="Model artifact"><ModelPicker models={models} selectedModel={selectedModel} onChange={(id) => { setSelectedModel(id); const found = models.find((m) => m.id === id); setPrecision(found?.precisions?.[0] || 'fp8'); }} /></Field><Field label="Requested precision"><select value={precision} onChange={(e) => setPrecision(e.target.value)}>{(activeModel?.precisions || ['fp8']).map((item) => <option key={item} value={item}>{item.toUpperCase()}</option>)}</select></Field><Field label="Task category"><select value={category} onChange={(e) => setCategory(e.target.value)}><option value="classification">Classification</option><option value="extraction">Extraction</option><option value="reasoning">Reasoning</option><option value="generation">Generation</option></select></Field><Field label="Prompt"><textarea rows="3" value={prompt} onChange={(e) => setPrompt(e.target.value)} /></Field><div className="precision-strip">{(activeModel?.precisions || []).map((item) => <button key={item} className={precision === item ? 'selected' : ''} onClick={() => setPrecision(item)}>{item.toUpperCase()}</button>)}</div></>}
      <div className="action-row"><button className="button button-primary run-button" disabled={loading || !online} onClick={onRun}>{loading ? <LoaderCircle className="spin" size={16} /> : <Play size={15} fill="currentColor" />}{loading ? 'Running…' : runLabel}</button>{active === 'switching' && <button className="button button-secondary" disabled={loading || !online} onClick={onCompare}><GitCompareArrows size={15} /> Compare confidence</button>}<span className="keyboard-hint">Runs against local API</span></div>
    </section><section className="panel insight-panel"><div className="panel-heading"><div><h3>What this demonstrates</h3><p>Architecture notes</p></div><CircleHelp size={16} className="muted-icon" /></div><TrackInsights id={active} /></section></div>
    {error && <div className="inline-error"><CircleHelp size={16} />{error}</div>}
    <ResultPanel result={result} />
  </div>;
}

function Field({ label, children }) { return <label className="field"><span className="field-label">{label}</span>{children}</label>; }

function ModelPicker({ models, selectedModel, onChange }) {
  return <select value={selectedModel} onChange={(e) => onChange(e.target.value)}>{models.map((model) => <option key={model.id} value={model.id}>{model.display_name || model.id} · {model.provider} · {model.tier}</option>)}</select>;
}

function TrackInsights({ id }) {
  const insights = {
    jev: ['Extract structured decisions before the LLM path.', 'A mapped refund result uses the deterministic billing handler.', 'Trace shows Jev decisions, selected route, and model nodes.'],
    slm: ['Select a model from the live registry.', 'Compare output quality with the AgentEval suites.', 'Catalog quality/cost values are estimates until measured.'],
    edge: ['Privacy policy controls edge vs cloud placement.', 'Ollama is the included laptop/local provider.', 'Mobile runtimes need a separate adapter and device validation.'],
    switching: ['Low confidence can raise the quality bar.', 'Compare high and low confidence against the same task.', 'Retries and validator errors can escalate to another model.'],
    parallel: ['Independent tasks share an execution wave.', 'The scheduler records critical path duration.', 'The demo uses the real DAG scheduler with mock model calls.'],
    orchestration: ['Planner/worker relationships are represented as DAG nodes.', 'Compare hierarchical, pipeline, and swarm structures.', 'The sample plan is deterministic rather than an autonomous LLM.'],
    quantization: ['Choose precision supported by the selected model entry.', 'The trace records requested and verified precision separately.', 'Mock precision is a label; it is not a quantized artifact.'],
  };
  return <ul className="insight-list">{insights[id].map((line, index) => <li key={line}><span className="insight-check"><Check size={12} /></span><span>{line}</span></li>)}</ul>;
}

function ResultPanel({ result }) {
  if (!result) return <div className="result-placeholder"><span><Activity size={19} /></span><div><b>Simulation output will appear here</b><small>Run the configured scenario to inspect routing, metrics, and trace events.</small></div><ArrowDownRight size={16} /></div>;
  if (result.kind === 'eval') return <EvaluationResult run={result.data} />;
  if (result.kind === 'comparison') return <div className="panel result-panel"><div className="panel-heading"><div><h3>Confidence routing comparison</h3><p>Same request · confidence changed</p></div><span className="success-badge">COMPLETE</span></div><div className="comparison-cards">{result.rows.map((row) => <div key={row.label} className="comparison-card"><small>{row.label} · {Math.round(row.confidence * 100)}%</small><b>{row.route?.model_id || 'See route trace'}</b><span>{row.route?.rationale || 'Inspect API trace for decision.'}</span><span className="comparison-output"><strong>Final output</strong><br />{typeof row.result.result === 'string' ? row.result.result : JSON.stringify(row.result.result)}</span></div>)}</div><details className="trace-details"><summary>View raw traces</summary><pre>{JSON.stringify(result.rows.map((r) => r.result.trace), null, 2)}</pre></details></div>;
  const data = result.data;
  const trace = data.trace || {};
  const nodes = trace.nodes || [];
  const routeEvent = trace.events?.find((event) => event.routes)?.routes || {};
  const routeRows = Object.entries(routeEvent);
  const jevEntries = Object.entries(trace.jev_decisions || {});
  const totalCost = nodes.reduce((sum, node) => sum + Number(node.cost_usd || 0), 0);
  return <div className="panel result-panel">
    <div className="panel-heading"><div><div className="eyebrow">SIMULATION RESULT</div><h3>{data.status === 'succeeded' ? 'Request completed' : 'Request finished'}</h3><p>{trace.routing_path || 'Routing trace recorded'} · {data.request_id?.slice(0, 8)}</p></div><span className="success-badge"><span className="status-dot online" /> SUCCESS</span></div>
    <div className="result-metrics"><span><small>Execution nodes</small><b>{nodes.length}</b></span><span><small>Critical path</small><b>{fmtMs(trace.critical_path_latency_ms)}</b></span><span><small>Estimated cost</small><b>{fmtCurrency(totalCost)}</b></span><span><small>Model nodes</small><b>{nodes.length}</b></span></div>
    <div className="journey-heading"><div><div className="eyebrow">DECISION-TO-RESULT</div><h4>Simulation journey</h4></div><span className="journey-id">{trace.request_id?.slice(0, 8) || data.request_id?.slice(0, 8)}</span></div>
    <div className="journey-grid">
      <JourneyStep number="01" title="Request understood" icon={Search} tint="violet">
        {jevEntries.length ? jevEntries.map(([key, decision]) => <p key={key}><b>{key.replaceAll('_', ' ')}</b> → {String(decision.choice)} <small>{Math.round(Number(decision.confidence || 0) * 100)}% confidence</small></p>) : <p>Task category: <b>{trace.routing_path?.startsWith('jev') ? 'structured decision' : 'agent task'}</b></p>}
      </JourneyStep>
      <JourneyStep number="02" title="Route selected" icon={GitCompareArrows} tint="blue">
        <p className="journey-main-value">{trace.routing_path || 'Model strategy'}</p>
        {routeRows.length ? routeRows.map(([id, route]) => <p className="journey-subline" key={id}><b>{id}</b>: {route.strategy || 'route'} · {route.placement || 'provider route'}{route.placement_rationale ? ` · ${route.placement_rationale}` : ''}</p>) : <p>{nodes.length ? 'Rule / tool handler selected before model execution.' : 'No model route was required for this result.'}</p>}
      </JourneyStep>
      <JourneyStep number="03" title="Model selected" icon={Bot} tint="teal">
        {nodes.length ? nodes.map((node) => <p key={node.node_id}><b>{node.node_id}</b> → {node.model_id || 'model'} <small>{node.provider || 'provider'} · {node.tier || 'tier'} · {node.precision_requested || node.precision || 'precision unknown'}{node.precision_verified ? ' · verified' : ''}</small></p>) : <p><b>0 platform model nodes</b><small> Direct rule result returned from the structured decision path.</small></p>}
      </JourneyStep>
      <JourneyStep number="04" title="Execution & final answer" icon={BadgeCheck} tint="amber">
        {nodes.length ? nodes.map((node) => <p key={node.node_id}><b>{node.node_id}</b> · {fmtMs(node.latency_ms)} · {fmtCurrency(node.cost_usd)}<small>{String(node.output ?? '').slice(0, 140)}</small></p>) : <p>The billing rule completed without calling a platform model.</p>}
      </JourneyStep>
    </div>
    <div className="result-output"><span className="output-label">FINAL RESULT</span><p>{typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2)}</p></div>
    <details className="trace-details"><summary>Inspect full execution trace <ChevronDown size={14} /></summary><pre>{JSON.stringify(trace, null, 2)}</pre></details>
  </div>;
}

function JourneyStep({ number, title, icon: Icon, tint, children }) {
  return <section className="journey-step"><div className="journey-step-head"><span className="journey-number">{number}</span><IconMark icon={Icon} tint={tint} size={28} /><b>{title}</b></div><div className="journey-step-body">{children}</div></section>;
}

function EvalView({ suites, suiteId, setSuiteId, selectedSuite, agentVersion, setAgentVersion, runs, loading, result, error, onRun }) {
  return <div className="content-page track-page"><div className="welcome-row"><div><div className="eyebrow"><span className="eyebrow-line" /> QUALITY GATES</div><h1>Agent evaluation</h1><p>Run a versioned suite, inspect case-level judgments, and compare release outcomes.</p></div><span className="mock-badge"><FlaskConical size={13} /> DETERMINISTIC DEMO</span></div><div className="track-layout"><section className="panel config-panel"><div className="panel-heading"><div><h3>Configure evaluation</h3><p>YAML suite · JSON history · audit rationales</p></div><IconMark icon={ShieldCheck} tint="teal" /></div><Field label="Evaluation suite"><select value={suiteId} onChange={(e) => setSuiteId(e.target.value)}>{suites.map((suite) => <option key={suite.id} value={suite.id}>{suite.name} · {suite.case_count} cases</option>)}</select></Field><Field label="Agent / prompt version"><select value={agentVersion} onChange={(e) => setAgentVersion(e.target.value)}><option value="demo-v1">demo-v1 · expected outputs</option><option value="demo-regressed">demo-regressed · show failures</option></select></Field>{selectedSuite && <div className="suite-summary"><span className="suite-badge">{selectedSuite.type}</span><b>{selectedSuite.description}</b><small>{selectedSuite.case_count} test cases · versioned YAML suite</small></div>}<button className="button button-primary run-button full" disabled={loading || !suites.length} onClick={onRun}>{loading ? <LoaderCircle className="spin" size={16} /> : <Play size={15} fill="currentColor" />}{loading ? 'Evaluating…' : 'Run evaluation suite'}</button>{error && <div className="inline-error compact">{error}</div>}</section><section className="panel insight-panel"><div className="panel-heading"><div><h3>Evaluation dimensions</h3><p>Auditable quality checks</p></div><BadgeCheck size={17} className="muted-icon" /></div><div className="dimension-list">{[['Task success','Exact, regex, or schema checks'],['Tool correctness','Name, arguments, and order'],['Groundedness','Claims vs retrieved context'],['Policy compliance','PII, actions, and spend caps'],['Latency & cost','p50 / p95, tokens, USD']].map(([name, desc]) => <div key={name}><span className="dimension-check"><Check size={12} /></span><span><b>{name}</b><small>{desc}</small></span></div>)}</div></section></div>{result && <ResultPanel result={result} />}<div className="section-heading compact-heading"><div><div className="eyebrow">RUN HISTORY</div><h2>Recent evaluations</h2></div><span className="section-extra">{runs.length} saved runs</span></div>{runs.length ? <div className="panel history-panel"><table><thead><tr><th>SUITE</th><th>VERSION</th><th>SUCCESS</th><th>COST</th><th>RUN ID</th></tr></thead><tbody>{[...runs].slice(-8).reverse().map((run) => <tr key={run.run_id}><td><b>{run.suite}</b></td><td>{run.agent_version}</td><td><span className={`score-pill ${run.summary?.success_rate < 1 ? 'low' : ''}`}>{Math.round((run.summary?.success_rate || 0) * 100)}%</span></td><td>{fmtCurrency(run.summary?.cost_usd)}</td><td className="mono">{run.run_id?.slice(0, 8)}</td></tr>)}</tbody></table></div> : <div className="result-placeholder"><span><Clock3 size={18} /></span><div><b>No evaluation history yet</b><small>Run a suite to populate the release comparison list.</small></div></div>}</div>;
}

function EvaluationResult({ run }) {
  const s = run.summary || {};
  return <div className="panel result-panel"><div className="panel-heading"><div><div className="eyebrow">EVALUATION REPORT</div><h3>{run.suite} · {run.agent_version}</h3><p>Run {run.run_id?.slice(0, 8)} · {new Date(run.started_at).toLocaleString()}</p></div><span className={`success-badge ${s.failed ? 'warning' : ''}`}>{s.failed ? 'GATE REVIEW' : 'PASSED'}</span></div><div className="result-metrics"><span><small>Task success</small><b>{Math.round((s.success_rate || 0) * 100)}%</b></span><span><small>Tool accuracy</small><b>{Math.round((s.tool_accuracy || 0) * 100)}%</b></span><span><small>Groundedness</small><b>{Math.round((s.groundedness || 0) * 100)}%</b></span><span><small>p95 latency</small><b>{fmtMs(s.p95_latency_ms)}</b></span><span><small>Cost</small><b>{fmtCurrency(s.cost_usd)}</b></span></div><div className="case-results">{(run.results || []).map((item) => <div className="case-row" key={item.case_id}><span className={`case-mark ${item.passed ? '' : 'fail'}`}>{item.passed ? <Check size={12} /> : <CircleHelp size={12} />}</span><div><b>{item.name}</b><small>{item.policy?.rationale || item.tool_use?.rationale || 'Deterministic assertions evaluated.'}</small><details className="case-detail"><summary>Input, output & judgments</summary><pre>{JSON.stringify({ input: item.input, output: item.output, checks: item.checks, tool_use: item.tool_use, groundedness: item.groundedness, policy: item.policy, steps: item.steps }, null, 2)}</pre></details></div><span className={`score-pill ${item.passed ? '' : 'low'}`}>{item.passed ? 'PASS' : 'FAIL'}</span></div>)}</div><details className="trace-details"><summary>Download / inspect JSON result</summary><pre>{JSON.stringify(run, null, 2)}</pre></details></div>;
}

function buildRequest(track, state) {
  const { prompt, category, confidence, selectedModel, precision, privacy, pattern, models } = state;
  if (track === 'jev') return { input: prompt, task_category: 'classification' };
  if (track === 'edge') return { input: prompt, task_category: category, privacy };
  if (track === 'switching') return { input: prompt, task_category: category, strategy: 'confidence_based', metadata: { confidence } };
  if (track === 'slm') return { input: prompt, task_category: category, metadata: { subtasks: [{ node_id: 'slm-candidate', task: prompt, input: prompt, task_category: category, model_id: selectedModel, precision: models.find((model) => model.id === selectedModel)?.precisions?.[0] }] } };
  if (track === 'quantization') return { input: prompt, task_category: category, metadata: { subtasks: [{ node_id: 'precision-candidate', task: prompt, input: prompt, task_category: category, model_id: selectedModel, precision }] } };
  let nodes;
  if (track === 'parallel') nodes = [
    { node_id: 'research', task: 'Retrieve facts for: ' + prompt, input: 'Retrieve facts for: ' + prompt, task_category: 'extraction' },
    { node_id: 'risk', task: 'Check risks for: ' + prompt, input: 'Check risks for: ' + prompt, task_category: 'classification' },
    { node_id: 'cost', task: 'Estimate costs for: ' + prompt, input: 'Estimate costs for: ' + prompt, task_category: 'computation' },
    { node_id: 'synthesis', task: 'Synthesize the completed work', input: 'Synthesize the completed work', task_category: 'generation', depends_on: ['research', 'risk', 'cost'] },
  ];
  else if (pattern === 'pipeline') nodes = [
    { node_id: 'research', task: 'Research: ' + prompt, task_category: 'extraction' },
    { node_id: 'analysis', task: 'Analyze research', task_category: 'reasoning', depends_on: ['research'] },
    { node_id: 'response', task: 'Draft final response', task_category: 'generation', depends_on: ['analysis'] },
  ];
  else if (pattern === 'swarm') nodes = [
    { node_id: 'research-agent', task: 'Research: ' + prompt, task_category: 'extraction' },
    { node_id: 'risk-agent', task: 'Review safety and policy', task_category: 'classification' },
    { node_id: 'analysis-agent', task: 'Analyze implications', task_category: 'reasoning' },
    { node_id: 'coordinator', task: 'Combine peer findings', task_category: 'generation', depends_on: ['research-agent', 'risk-agent', 'analysis-agent'] },
  ];
  else nodes = [
    { node_id: 'planner', task: 'Plan work for: ' + prompt, task_category: 'classification' },
    { node_id: 'researcher', task: 'Find supporting facts', task_category: 'extraction', depends_on: ['planner'] },
    { node_id: 'analyst', task: 'Analyze the task', task_category: 'reasoning', depends_on: ['planner'] },
    { node_id: 'synthesizer', task: 'Combine findings', task_category: 'generation', depends_on: ['researcher', 'analyst'] },
  ];
  return { input: prompt, task_category: 'generation', metadata: { subtasks: nodes } };
}

class RenderBoundary extends React.Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error('React page render failed', error, info.componentStack); }
  render() {
    if (this.state.error) return <main className="fatal-error"><div className="fatal-card"><CircleHelp size={24} /><div><h1>This simulation screen hit a rendering error</h1><p>{this.state.error.message}</p><small>Refresh the page after checking the browser console. The rest of the app remains available.</small><button className="button button-primary" onClick={() => this.setState({ error: null })}>Try rendering again</button></div></div></main>;
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(<React.StrictMode><RenderBoundary><App /></RenderBoundary></React.StrictMode>);

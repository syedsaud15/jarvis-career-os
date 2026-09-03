import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import './App.rebuild.css'
import { demoData } from './demoData'
import CareerInsights from './CareerInsights'
import CareerActivity from './CareerActivity'

const stages = ['SAVED', 'APPLIED', 'INTERVIEW', 'REJECTED']
const navItems = [
  ['overview', '⌂', 'Overview'],
  ['opportunities', '◇', 'Opportunities'],
  ['pipeline', '▥', 'Pipeline'],
  ['actions', '↗', 'Action center'],
  ['insights', '◎', 'Insights & settings'],
]

const demoNavItems = [...navItems, ['showcase', '⌘', 'Project showcase'], ['privacy', '◉', 'Privacy & safety']]

function ReactorMark() {
  return <div className="system-orb reactor-vector" aria-label="JARVIS intelligence core online"><svg viewBox="0 0 160 160" role="img" aria-label="Original JARVIS intelligence core"><defs><linearGradient id="core" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#3ee7e0"/><stop offset=".52" stopColor="#418fe8"/><stop offset="1" stopColor="#7667db"/></linearGradient></defs><circle cx="80" cy="80" r="66"/><circle cx="80" cy="80" r="52"/><path d="M80 25 128 52 128 108 80 135 32 108 32 52Z"/><path d="M80 43 111 61 111 98 80 117 49 98 49 61Z"/><path className="core-glyph" d="M52 58h18l10 39 10-39h18L92 110H68Z"/></svg><i><span />JARVIS INTELLIGENCE</i></div>
}

function PageHeader({ kicker, title, copy, action }) {
  return <header className="page-heading"><div><span>{kicker}</span><h1 tabIndex={-1}>{title}</h1><p>{copy}</p></div>{action}</header>
}

function formatTimestamp(value) {
  if (!value) return '—'
  // SQLite timestamps are UTC without an offset; PostgreSQL includes its offset.
  const normalized = String(value).replace(' ', 'T')
  const parsed = new Date(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?$/.test(normalized) ? `${normalized}Z` : normalized)
  return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleString()
}

async function apiRequest(url, options = {}, timeout = 20000) {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `Request failed (${response.status})`)
    }
    return response
  } finally {
    window.clearTimeout(timer)
  }
}

function App() {
  const isDemo = window.location.pathname.startsWith('/demo')
  const [page, setPage] = useState('overview')
  const [jobFilter, setJobFilter] = useState('all')
  const [query, setQuery] = useState('find senior data engineer jobs in Pune')
  const [jobs, setJobs] = useState([])
  const [applications, setApplications] = useState([])
  const [profile, setProfile] = useState({ resume_connected: false, skills: [] })
  const [analytics, setAnalytics] = useState({ interview_rate: 0, open_follow_ups: [] })
  const [integrations, setIntegrations] = useState([])
  const [alerts, setAlerts] = useState([])
  const [approvals, setApprovals] = useState([])
  const [notifications, setNotifications] = useState([])
  const [activity, setActivity] = useState([])
  const [settings, setSettings] = useState({ display_name: 'Syed Saud', target_role: 'Data Engineer', target_location: 'Pune', minimum_fit: 45, weekly_digest: true, follow_up_reminders: true })
  const [weekly, setWeekly] = useState(null)
  const [email, setEmail] = useState({ to: '', subject: '', body: '' })
  const [event, setEvent] = useState({ title: '', starts_at: '', ends_at: '' })
  const [selected, setSelected] = useState(null)
  const [notes, setNotes] = useState([])
  const [note, setNote] = useState('')
  const [followUp, setFollowUp] = useState('')
  const [coverLetter, setCoverLetter] = useState('')
  const [interviewPrep, setInterviewPrep] = useState(null)
  const [copilot, setCopilot] = useState(null)
  const [busy, setBusy] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [apiOnline, setApiOnline] = useState(true)
  const [lastSynced, setLastSynced] = useState(null)
  const [decisionBusy, setDecisionBusy] = useState(null)
  const [notice, setNotice] = useState('All systems operational')
  const [filters, setFilters] = useState({ location: 'ALL', workMode: 'ALL', experience: 'ALL', freshness: 'ALL', salary: 0 })
  const scanInputRef = useRef(null)
  const previousPageRef = useRef(page)
  const resumeInputRef = useRef(null)
  const workspaceRef = useRef(null)
  const workspaceTriggerRef = useRef(null)
  const [roadmap, setRoadmap] = useState(null)
  const [trends, setTrends] = useState(null)

  const saved = useMemo(() => new Set(applications.map((item) => item.job_listing_id)), [applications])
  const averageFit = jobs.length ? Math.round(jobs.reduce((sum, job) => sum + job.match_score, 0) / jobs.length) : 0
  const pipeline = useMemo(() => Object.fromEntries(stages.map((stage) => [stage, applications.filter((item) => item.status === stage)])), [applications])
  const signals = useMemo(() => Object.entries(jobs.flatMap((job) => job.matched_skills || []).reduce((all, skill) => ({ ...all, [skill]: (all[skill] || 0) + 1 }), {})).sort((a, b) => b[1] - a[1]).slice(0, 6), [jobs])
  const locations = useMemo(() => [...new Set(jobs.map((job) => (job.location || '').split(',')[0]).filter(Boolean))].sort(), [jobs])
  const visibleJobs = useMemo(() => jobs.filter((job) => {
    if (jobFilter === 'high' && job.match_score < 45) return false
    if (jobFilter === 'mnc' && !job.mnc_priority) return false
    if (filters.location !== 'ALL' && !(job.location || '').toLowerCase().includes(filters.location.toLowerCase())) return false
    if (filters.workMode !== 'ALL' && job.work_mode !== filters.workMode) return false
    if (filters.experience !== 'ALL' && job.experience_level !== filters.experience) return false
    if (filters.freshness !== 'ALL' && Number(job.age_days ?? 999) > Number(filters.freshness)) return false
    if (filters.salary && Number(job.salary_max || job.salary_min || 0) < filters.salary * 100000) return false
    return !job.is_expired
  }).sort((a, b) => (b.match_score + (b.quality_score || 0) / 10) - (a.match_score + (a.quality_score || 0) / 10)), [jobs, jobFilter, filters])
  const greeting = useMemo(() => { const hour = new Date().getHours(); return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening' }, [])

  const loadData = useCallback(async (showStatus = false) => {
    if (isDemo) {
      setJobs(demoData.jobs); setApplications(demoData.applications); setProfile(demoData.profile); setAnalytics(demoData.analytics); setIntegrations(demoData.integrations); setAlerts(demoData.alerts); setApprovals(demoData.approvals); setNotifications(demoData.notifications); setActivity(demoData.activity); setSettings(demoData.settings); setWeekly(demoData.weekly); setRoadmap(demoData.roadmap); setTrends(demoData.trends); setApiOnline(true); setLastSynced(new Date()); setSyncing(false); if (showStatus) setNotice('Demo intelligence refreshed — no live data changed'); return
    }
    setSyncing(true)
    if (showStatus) setNotice('Synchronizing career intelligence…')
    try {
      const urls = ['/api/jobs?limit=100', '/api/applications', '/api/profile', '/api/analytics', '/api/integrations', '/api/alerts', '/api/approvals', '/api/notifications', '/api/activity', '/api/settings', '/api/reports/weekly', '/api/profile/skill-roadmap', '/api/analytics/trends']
      const responses = await Promise.all(urls.map((url) => apiRequest(url, { cache: 'no-store' })))
      const data = await Promise.all(responses.map((response) => response.json()))
      setJobs(data[0]); setApplications(data[1]); setProfile(data[2]); setAnalytics(data[3]); setIntegrations(data[4]); setAlerts(data[5]); setApprovals(data[6]); setNotifications(data[7]); setActivity(data[8]); setSettings(data[9]); setWeekly(data[10]); setRoadmap(data[11]); setTrends(data[12])
      setApiOnline(true); setLastSynced(new Date())
      if (showStatus) setNotice('Career intelligence synchronized')
    } catch (error) {
      setApiOnline(false); setNotice(error.name === 'AbortError' ? 'API request timed out' : error.message)
      throw error
    } finally { setSyncing(false) }
  }, [isDemo])

  useEffect(() => {
    const initial = window.setTimeout(() => { void loadData().catch(() => {}) }, 0)
    const refresh = window.setInterval(() => { void loadData().catch(() => {}) }, 60000)
    return () => { window.clearTimeout(initial); window.clearInterval(refresh) }
  }, [loadData])
  useEffect(() => {
    const onKeyDown = (eventObject) => {
      if ((eventObject.ctrlKey || eventObject.metaKey) && eventObject.key.toLowerCase() === 'k') {
        eventObject.preventDefault(); setPage('overview'); window.setTimeout(() => scanInputRef.current?.focus(), 0)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'auto' })
    if (previousPageRef.current !== page) document.querySelector('main h1')?.focus({ preventScroll: true })
    previousPageRef.current = page
  }, [page])
  useEffect(() => {
    if (selected) workspaceRef.current?.focus()
  }, [selected])
  function closeWorkspace() { setSelected(null); workspaceTriggerRef.current?.focus() }

  async function scan(eventObject) {
    eventObject.preventDefault(); if (!query.trim() || busy) return
    if (isDemo) { setNotice('Demo scan complete — sample signals refreshed safely'); setPage('opportunities'); return }
    setBusy(true); setNotice('Scanning live market signals…')
    try {
      await apiRequest('/api/process', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: query, sender: 'dashboard-user' }) }, 90000)
      await loadData(); setNotice('Opportunity map updated'); setPage('opportunities')
    } catch (error) { setNotice(error.message || 'Scan interrupted — check backend') } finally { setBusy(false) }
  }
  async function saveJob(id) { if (isDemo) { setNotice('Read-only demo: capture is simulated'); return } const response = await fetch('/api/applications', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job_listing_id: id, sender: 'dashboard-user' }) }); if (response.ok) await loadData() }
  async function moveApplication(id, status) { if (isDemo) { setNotice('Read-only demo: pipeline updates are disabled'); return } const response = await fetch(`/api/applications/${id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) }); if (response.ok) await loadData() }
  async function uploadResume(e) { const file = e.target.files?.[0]; if (!file) return; const body = new FormData(); body.append('file', file); setNotice('Analyzing resume…'); const response = await fetch('/api/profile/upload', { method: 'POST', body }); if (response.ok) { await loadData(); setNotice('Resume intelligence updated') } else setNotice('Resume upload failed') }
  async function connectGoogle() { const response = await fetch('/api/integrations/google/start'); const result = await response.json().catch(() => ({})); if (response.ok) window.location.assign(result.authorization_url); else setNotice(result.detail || 'Google connection failed') }
  async function requestEmail(e) { e.preventDefault(); const response = await fetch('/api/actions/email/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(email) }); if (response.ok) { setEmail({ to: '', subject: '', body: '' }); await loadData(); setNotice('Email queued for approval') } }
  async function requestEvent(e) { e.preventDefault(); if (new Date(event.ends_at) <= new Date(event.starts_at)) { setNotice('End time must be after start time'); return } const response = await fetch('/api/actions/calendar/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(event) }); if (response.ok) { setEvent({ title: '', starts_at: '', ends_at: '' }); await loadData(); setNotice('Calendar event queued for approval') } }
  async function decide(id, decision) { setDecisionBusy(id); try { const response = await apiRequest(`/api/approvals/${id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }) }, 60000); const result = await response.json().catch(() => ({})); setNotice(result.execution || `Action ${decision.toLowerCase()}`); await loadData() } catch (error) { setNotice(error.message) } finally { setDecisionBusy(null) } }
  async function openWorkspace(item) { workspaceTriggerRef.current = document.activeElement; setSelected(item); setNotes([]); setCopilot(null); setCoverLetter('Loading draft…'); setInterviewPrep(null); setPage('pipeline'); if (isDemo) { const job = jobs.find((candidate) => candidate.id === item.job_listing_id); const prep = { matched_strengths: job?.matched_skills || ['python','sql'], skill_gaps: job?.missing_skills || [], questions: ['Describe a production pipeline failure you diagnosed and prevented from recurring.', 'How would you design data-quality checks for a critical business dataset?', 'Which reliability metrics would you expose to operators and stakeholders?'] }; const letter = `Dear Hiring Team,\n\nI am interested in the ${item.title} opportunity at ${item.company}. My experience building reliable Python, SQL and cloud data pipelines aligns with the role's core outcomes. I would welcome the chance to discuss measurable improvements I have delivered across orchestration, quality and observability.\n\nRegards,\nDemo Candidate`; setNotes([{ id: 'demo-note', body: 'Prepared STAR examples for pipeline reliability and data-quality ownership.' }]); setCoverLetter(letter); setInterviewPrep(prep); setCopilot({ resume_suggestions: ['Lead with a quantified pipeline reliability result.', 'Map Python, SQL and cloud evidence to the role requirements.', 'Add one measurable data-quality achievement.'], recruiter_email: `Subject: ${item.title} opportunity\n\nHello, my production data-engineering experience aligns with this role. I would value a brief conversation about your team's priorities.` }); return } try { const [notesResponse, copilotResponse] = await Promise.all([apiRequest(`/api/applications/${item.id}/notes`), apiRequest(`/api/applications/${item.id}/copilot`)]); if (notesResponse.ok) setNotes(await notesResponse.json()); if (copilotResponse.ok) { const result = await copilotResponse.json(); setCopilot(result); setCoverLetter(result.cover_letter); setInterviewPrep(result.interview_prep) } } catch (error) { setNotice(error.message); setCoverLetter('Could not load this workspace. Close it and retry.') } }
  function exportDemoCsv() { const rows = [['status','title','company','location'], ...applications.map((item) => [item.status,item.title,item.company,item.location])]; const csvText = rows.map((row) => row.map((value) => `"${String(value || '').replaceAll('"','""')}"`).join(',')).join('\n'); const link = document.createElement('a'); link.href = URL.createObjectURL(new Blob([csvText], { type: 'text/csv' })); link.download = 'jarvis-demo-applications.csv'; link.click(); URL.revokeObjectURL(link.href) }
  async function addNote(e) { e.preventDefault(); if (isDemo) { setNotice('Read-only demo: notes are not stored'); return } if (!selected || !note.trim()) return; const response = await fetch(`/api/applications/${selected.id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ body: note }) }); if (response.ok) { setNotes([await response.json(), ...notes]); setNote('') } }
  async function scheduleFollowUp(e) { e.preventDefault(); if (isDemo) { setNotice('Read-only demo: reminders are not stored'); return } if (!selected || !followUp) return; const response = await fetch(`/api/applications/${selected.id}/follow-ups`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ due_on: followUp }) }); if (response.ok) { setFollowUp(''); await loadData(); setNotice('Follow-up scheduled') } }
  async function saveSettings(e) { e.preventDefault(); if (isDemo) { setNotice('Read-only demo: preferences remain unchanged'); return } try { const response = await apiRequest('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings) }); setSettings(await response.json()); setNotice('Career preferences saved') } catch (error) { setNotice(error.message) } }

  const activeNav = isDemo ? demoNavItems : navItems
  return <div className={`jarvis-app ${isDemo ? 'demo-mode' : 'personal-mode'}`}>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className="side-rail">
      <button className="brand" onClick={() => setPage('overview')}><b>J</b><span>JARVIS<small>CAREER INTELLIGENCE</small></span></button>
      <nav aria-label="Main navigation">{activeNav.map(([id, icon, label]) => <button key={id} aria-label={label} aria-current={page === id ? 'page' : undefined} title={label} className={page === id ? 'active' : ''} onClick={() => setPage(id)}><i>{icon}</i><span>{label}</span>{id === 'actions' && approvals.length > 0 && <em>{approvals.length}</em>}</button>)}</nav>
      <div className="rail-card"><span>{isDemo ? 'DEMO PROFILE' : 'PROFILE ENGINE'}</span><strong>{profile.resume_connected ? 'Resume online' : 'Resume needed'}</strong><small>{profile.skills?.length || 0} skills mapped</small><button disabled={isDemo} onClick={() => resumeInputRef.current?.click()}>{isDemo ? 'Read-only demo' : profile.resume_connected ? 'Update resume' : 'Add resume'}</button>{!isDemo && <input ref={resumeInputRef} type="file" aria-label="Upload resume" accept=".pdf,.txt" onChange={uploadResume} />}</div>
      <footer><span className="avatar">{isDemo ? 'DC' : 'SS'}</span><div><b>{isDemo ? 'Demo Candidate' : 'Syed Saud'}</b><small>{isDemo ? 'Read-only workspace' : 'Data Engineer'}</small></div><i>•••</i></footer>
    </aside>

    <main id="main-content" tabIndex={-1} className="product-area">
      <div className="hud-atmosphere" aria-hidden="true">
        <svg viewBox="0 0 1400 900" preserveAspectRatio="xMidYMid slice">
          <g className="hud-orbits"><circle cx="1135" cy="210" r="118"/><circle cx="1135" cy="210" r="82"/><circle cx="1135" cy="210" r="46"/><path d="M940 210h84m222 0h102M1135 14v72m0 248v96"/></g>
          <g className="hud-schematic"><path d="M90 680h160l55-55h175l48-48h150"/><path d="M770 690h142l42-42h182l64-64h126"/><path d="M210 130h126l44 44h134"/><circle cx="250" cy="680" r="7"/><circle cx="528" cy="577" r="7"/><circle cx="954" cy="648" r="7"/><circle cx="1200" cy="584" r="7"/></g>
          <g className="hud-mechanics"><path d="M72 300h125m-102 16h76m-54 16h32"/><path d="M1288 420h54m-84 16h84m-112 16h112"/><circle cx="520" cy="760" r="36"/><circle cx="520" cy="760" r="20"/><path d="M520 710v22m0 56v22m-50-50h22m56 0h22"/></g>
        </svg>
        <span className="hud-code code-a">JRV.OS / CAREER-INTEL / 06</span>
        <span className="hud-code code-b">PROFILE VECTOR // ACTIVE</span>
        <span className="hud-code code-c">SIGNAL BUS 01 · SECURE</span>
      </div>
      <div className="topbar"><div className={`status-pill ${apiOnline ? '' : 'offline'}`} role="status" aria-live="polite"><i />{isDemo ? 'Public demo · private integrations isolated' : notice}{lastSynced && <small> · {lastSynced.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>}</div><div className="top-actions">{isDemo && <span className="demo-badge">READ ONLY</span>}{notifications.length > 0 && <button type="button" onClick={() => setPage('insights')}>Alerts {notifications.length}</button>}<button type="button" disabled={syncing} onClick={() => void loadData(true).catch(() => {})}>{syncing ? 'Syncing…' : 'Sync data'}</button><button type="button" className="command-key" aria-label="Focus intelligence scan" onClick={() => { setPage('overview'); window.setTimeout(() => scanInputRef.current?.focus(), 0) }}>⌘ K</button></div></div>

      {page === 'overview' && <section className="page overview-page">
        <PageHeader kicker={isDemo ? 'PUBLIC PRODUCT EXPERIENCE' : 'CAREER COMMAND CENTER'} title={<>{greeting}, {isDemo ? 'Explorer' : 'Syed'}.<br/><em>Your next move is getting clearer.</em></>} copy={isDemo ? 'Explore a safe, fully populated product simulation. No private data or real integrations are used.' : 'A live operating picture of your market, profile and active opportunities.'} action={<ReactorMark />} />
        <form className="scan-bar" onSubmit={scan}><span aria-hidden="true">⌕</span><label className="sr-only" htmlFor="career-scan">Career intelligence query</label><input id="career-scan" ref={scanInputRef} value={query} onChange={(e) => setQuery(e.target.value)} autoComplete="off" /><button disabled={busy}>{busy ? 'Scanning market…' : 'Run intelligence scan'} ↗</button></form>
        <div className="metric-grid"><article><span>Market signals</span><strong>{jobs.length}</strong><small>{profile.skills?.length || 0} profile skills mapped</small></article><article><span>Average fit</span><strong>{averageFit || '—'}{averageFit ? '%' : ''}</strong><small>Across live roles</small></article><article><span>Active pipeline</span><strong>{applications.length}</strong><small>{analytics.interview_rate}% interview rate</small></article><article><span>Pending actions</span><strong>{approvals.length}</strong><small>Approval protected</small></article></div>
        <div className="overview-grid">
          <section className="panel market-panel"><header><div><span>MARKET PULSE</span><h2>Skills creating leverage</h2></div><button onClick={() => setPage('opportunities')}>Explore roles ↗</button></header><div className="signal-chart">{signals.map(([skill, count], index) => <div key={skill}><span>0{index + 1}</span><b>{skill}</b><i><u style={{width:`${Math.min(100, 35 + count * 13)}%`}} /></i><em>{count} signals</em></div>)}{!signals.length && <p>No matching skill signals in these listings yet. Scan more roles and review their full descriptions; this does not mean your resume has no skills.</p>}</div></section>
          <section className="panel radar-panel"><header><span>HIGH-FIT RADAR</span><b>{alerts.length} SIGNALS</b></header>{alerts.slice(0, 3).map((alert) => <article key={`${alert.title}-${alert.company}`}><div className="score-ring">{alert.match_score}%</div><div><strong>{alert.title}</strong><small>{alert.company}</small></div></article>)}{!alerts.length && <div className="panel-empty">No uncaptured roles meet the 45% radar threshold. Try a broader scan.</div>}</section>
          <CareerActivity trends={trends} isDemo={isDemo} onDetails={() => setPage('insights')} />
        </div>
        <section className="panel integration-panel"><div><span>CONNECTED WORKSPACE</span><h2>Your career stack, synchronized.</h2></div><div className="integration-row">{integrations.map((item) => <div key={item.name} className={item.status === 'CONNECTED' ? 'online' : ''}><i>{item.name.includes('Gmail') ? 'M' : item.name.includes('Calendar') ? '31' : 'A'}</i><span><b>{item.name}</b><small>{item.status === 'CONNECTED' ? 'Connected' : 'Ready to connect'}</small></span></div>)}{integrations.some((item) => item.status === 'OAUTH_REQUIRED') && <button onClick={connectGoogle}>Connect Google</button>}</div></section>
      </section>}

      {page === 'opportunities' && <section className="page">
        <PageHeader kicker="OPPORTUNITY INTELLIGENCE" title="Roles worth your attention." copy="Ranked by evidence from your resume, market demand and employer quality." action={<button className="primary" onClick={() => setPage('overview')}>New scan ↗</button>} />
        <div className="filter-row"><button className={jobFilter === 'all' ? 'active' : ''} onClick={() => setJobFilter('all')}>All signals <b>{jobs.length}</b></button><button className={jobFilter === 'high' ? 'active' : ''} onClick={() => setJobFilter('high')}>High fit</button><button className={jobFilter === 'mnc' ? 'active' : ''} onClick={() => setJobFilter('mnc')}>MNC priority</button><span>{visibleJobs.length} roles · ranked by fit + quality</span></div>
        <div className="advanced-filters" aria-label="Advanced opportunity filters"><label>Location<select value={filters.location} onChange={(e) => setFilters({...filters,location:e.target.value})}><option value="ALL">India · all</option>{locations.map((location) => <option key={location}>{location}</option>)}</select></label><label>Work mode<select value={filters.workMode} onChange={(e) => setFilters({...filters,workMode:e.target.value})}><option value="ALL">All modes</option><option value="REMOTE">Remote</option><option value="HYBRID">Hybrid</option><option value="ONSITE">On-site</option></select></label><label>Experience<select value={filters.experience} onChange={(e) => setFilters({...filters,experience:e.target.value})}><option value="ALL">All levels</option><option value="ENTRY">Entry</option><option value="MID">Mid</option><option value="SENIOR">Senior</option></select></label><label>Freshness<select value={filters.freshness} onChange={(e) => setFilters({...filters,freshness:e.target.value})}><option value="ALL">Any date</option><option value="3">Last 3 days</option><option value="7">Last 7 days</option><option value="14">Last 14 days</option></select></label><label>Min salary<select value={filters.salary} onChange={(e) => setFilters({...filters,salary:Number(e.target.value)})}><option value="0">Any salary</option><option value="10">₹10L+</option><option value="15">₹15L+</option><option value="20">₹20L+</option></select></label></div>
        <div className="job-grid">{visibleJobs.map((job) => <article key={job.id} className="job-card"><header><div className="company-mark">{(job.company || 'J').charAt(0)}</div><div className="quality"><small>QUALITY</small><b>{job.quality_score || '—'}</b></div><div className="match"><strong>{job.match_score}%</strong><small>PROFILE FIT</small></div></header><span className="location">{job.location || 'Location flexible'} · {job.work_mode || 'FLEXIBLE'} · {job.experience_level || 'OPEN'}</span><h2>{job.title}</h2><p>{job.company || 'Employer signal'}</p><div className="chip-row">{(job.matched_skills || []).slice(0,4).map((skill) => <span key={skill}>{skill}</span>)}</div><small className="explain">{job.match_explanation}</small><footer>{job.redirect_url && !isDemo && <a href={job.redirect_url} target="_blank" rel="noreferrer">View role ↗</a>}<button disabled={isDemo || saved.has(job.id)} onClick={() => saveJob(job.id)}>{isDemo ? 'Demo only' : saved.has(job.id) ? 'Captured ✓' : 'Capture role'}</button></footer></article>)}</div>
        {!visibleJobs.length && <div className="results-empty"><b>No matching roles in this view.</b><span>Try another filter or run a fresh intelligence scan.</span><button onClick={() => { setJobFilter('all'); setFilters({ location: 'ALL', workMode: 'ALL', experience: 'ALL', freshness: 'ALL', salary: 0 }) }}>Show all opportunities</button></div>}
      </section>}

      {page === 'pipeline' && <section className="page">
        <PageHeader kicker="APPLICATION PIPELINE" title="Every opportunity, in motion." copy="Move roles forward and keep the next action visible." action={isDemo ? <button className="primary" onClick={exportDemoCsv}>Export sample CSV ↗</button> : <a className="primary" href="/api/applications/export.csv">Export CSV ↗</a>} />
        <div className="pipeline-board">{stages.map((stage) => <section key={stage}><header><span>{stage}</span><b>{pipeline[stage].length}</b></header>{pipeline[stage].map((item) => <article key={item.id}><strong>{item.title}</strong><small>{item.company}</small><button onClick={() => openWorkspace(item)}>Open workspace</button>{stage === 'SAVED' && <button disabled={isDemo} onClick={() => moveApplication(item.id, 'APPLIED')}>Mark applied →</button>}{stage === 'APPLIED' && <button disabled={isDemo} onClick={() => moveApplication(item.id, 'INTERVIEW')}>Move to interview →</button>}</article>)}{!pipeline[stage].length && <div className="drop-zone">No roles yet</div>}</section>)}</div>
        {selected && <section className="detail-drawer" ref={workspaceRef} tabIndex={-1} aria-label="Application workspace" onKeyDown={(e) => { if (e.key === 'Escape') closeWorkspace() }}><header><div><span>APPLICATION WORKSPACE</span><h2>{selected.title}</h2><p>{selected.company}</p></div><button aria-label="Close application workspace" onClick={closeWorkspace}>×</button></header><div className="detail-grid"><div><form onSubmit={addNote}><label>Private note<textarea disabled={isDemo} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Recruiter details, interview notes, next move…" /></label><button disabled={isDemo}>Add note</button></form><div className="notes-list">{notes.map((item) => <p key={item.id}>{item.body}</p>)}</div><form className="follow-form" onSubmit={scheduleFollowUp}><input aria-label="Follow-up date" disabled={isDemo} type="date" value={followUp} onChange={(e) => setFollowUp(e.target.value)} /><button disabled={isDemo}>Schedule follow-up</button></form></div><div className="draft"><span>TAILORED COVER LETTER</span><pre>{coverLetter}</pre>{copilot && <div className="copilot-block"><span>RESUME COPILOT</span>{copilot.resume_suggestions.map((tip) => <p key={tip}>{tip}</p>)}<b>RECRUITER EMAIL</b><pre>{copilot.recruiter_email}</pre></div>}{interviewPrep && <div className="prep-block"><span>INTERVIEW INTELLIGENCE</span><b>Strengths: {interviewPrep.matched_strengths.join(', ') || 'Build evidence from your projects'}</b><small>Gaps: {interviewPrep.skill_gaps.join(', ') || 'No critical skill gap detected'}</small>{interviewPrep.questions.map((question) => <p key={question}>{question}</p>)}{interviewPrep.preparation_plan && <ol>{interviewPrep.preparation_plan.map((step) => <li key={step}>{step}</li>)}</ol>}</div>}</div></div></section>}
      </section>}

      {page === 'actions' && <section className="page">
        <PageHeader kicker="APPROVAL-GATED AUTOMATION" title="You stay in control." copy="JARVIS prepares the work. Nothing is sent or scheduled without your approval." />
        {isDemo && <div className="safety-banner"><b>Safe simulation</b><span>Gmail and Calendar are disconnected from this public workspace. Forms are visible as product demonstrations only.</span></div>}
        <div className="action-grid"><form className="composer" onSubmit={requestEmail}><span>GMAIL COMPOSER</span><h2>Draft an outreach email</h2><input aria-label="Recipient email" type="email" placeholder="Recipient email" value={email.to} onChange={(e) => setEmail({...email,to:e.target.value})} required disabled={isDemo}/><input aria-label="Email subject" placeholder="Subject" value={email.subject} onChange={(e) => setEmail({...email,subject:e.target.value})} required disabled={isDemo}/><textarea aria-label="Email message" placeholder={isDemo ? 'Disabled in public demo' : 'Write your message…'} value={email.body} onChange={(e) => setEmail({...email,body:e.target.value})} required disabled={isDemo}/><button disabled={isDemo}>{isDemo ? 'Simulation only' : 'Send for approval ↗'}</button></form><form className="composer" onSubmit={requestEvent}><span>CALENDAR COMPOSER</span><h2>Schedule an interview</h2><input aria-label="Event title" placeholder="Event title" value={event.title} onChange={(e) => setEvent({...event,title:e.target.value})} required disabled={isDemo}/><label>Starts<input type="datetime-local" value={event.starts_at} onChange={(e) => setEvent({...event,starts_at:e.target.value})} required disabled={isDemo}/></label><label>Ends<input type="datetime-local" value={event.ends_at} onChange={(e) => setEvent({...event,ends_at:e.target.value})} required disabled={isDemo}/></label><button disabled={isDemo}>{isDemo ? 'Simulation only' : 'Send for approval ↗'}</button></form></div>
        <section className="approval-queue"><header><div><span>APPROVAL QUEUE</span><h2>Ready for your decision</h2></div><b>{approvals.length} pending</b></header>{approvals.map((item) => <article key={item.id}><div><i>↗</i><span><strong>{item.summary}</strong><small>{item.tool_name}</small></span></div><footer><button disabled={decisionBusy === item.id} onClick={() => decide(item.id,'REJECTED')}>Reject</button><button disabled={decisionBusy === item.id} onClick={() => decide(item.id,'APPROVED')}>{decisionBusy === item.id ? 'Executing…' : 'Approve & execute'}</button></footer></article>)}{!approvals.length && <div className="queue-empty">Everything is clear. No actions waiting.</div>}</section>
      </section>}

      {page === 'insights' && <section className="page">
        <PageHeader kicker="CAREER OPERATIONS" title="Your intelligence layer." copy="Preferences, reminders, weekly performance and a traceable activity history." />
        <div className="insight-grid">
          <form className="composer settings-form" onSubmit={saveSettings}><span>CAREER PREFERENCES</span><h2>Calibrate JARVIS</h2><input aria-label="Display name" value={settings.display_name} onChange={(e) => setSettings({...settings, display_name:e.target.value})} placeholder="Display name" required disabled={isDemo}/><input aria-label="Target role" value={settings.target_role} onChange={(e) => setSettings({...settings, target_role:e.target.value})} placeholder="Target role" required disabled={isDemo}/><input aria-label="Target location" value={settings.target_location} onChange={(e) => setSettings({...settings, target_location:e.target.value})} placeholder="Target location" required disabled={isDemo}/><label>Minimum profile fit<input type="number" min="0" max="100" value={settings.minimum_fit} onChange={(e) => setSettings({...settings, minimum_fit:Number(e.target.value)})} disabled={isDemo}/></label><label className="check"><input type="checkbox" checked={settings.weekly_digest} onChange={(e) => setSettings({...settings, weekly_digest:e.target.checked})} disabled={isDemo}/> Weekly intelligence digest</label><label className="check"><input type="checkbox" checked={settings.follow_up_reminders} onChange={(e) => setSettings({...settings, follow_up_reminders:e.target.checked})} disabled={isDemo}/> Follow-up reminders</label><button disabled={isDemo}>{isDemo ? 'Read-only demo' : 'Save preferences ↗'}</button></form>
          <section className="panel weekly-panel"><header><div><span>WEEKLY COMMAND BRIEF</span><h2>Momentum at a glance</h2></div></header>{weekly && <div className="weekly-stats"><article><strong>{weekly.new_applications}</strong><small>ROLES CAPTURED · 7 DAYS</small></article><article><strong>{weekly.interviews_moved}</strong><small>CURRENT INTERVIEWS UPDATED · 7 DAYS</small></article><article><strong>{weekly.interview_rate}%</strong><small>INTERVIEW RATE</small></article><p>{weekly.recommended_focus}</p></div>}<div className="funnel" aria-label="Application funnel">{(analytics.funnel || stages.map((stage) => ({stage,total:pipeline[stage].length}))).map((item) => <div key={item.stage}><span>{item.stage}</span><i><b style={{width:`${Math.max(0, (item.total / Math.max(1, applications.length)) * 100)}%`}} /></i><strong>{item.total}</strong></div>)}</div><div className="notification-list">{notifications.map((item) => <article key={item.id}><b>{item.title}</b><small>{item.detail}</small></article>)}{!notifications.length && <p>All clear. No reminders need attention.</p>}</div></section>
        </div>
        <CareerInsights roadmap={roadmap} trends={trends} isDemo={isDemo} onUploadResume={() => resumeInputRef.current?.click()} />
        <section className="approval-queue activity-log"><header><div><span>AUDIT & ACTIVITY</span><h2>Everything JARVIS has touched</h2></div><b>{activity.length} events</b></header>{activity.slice(0,20).map((item, index) => <article key={`${item.created_at}-${index}`}><div><i>◎</i><span><strong>{item.type.replaceAll('.', ' ')}</strong><small>{item.details}</small></span></div><time>{formatTimestamp(item.created_at)}</time></article>)}{!activity.length && <div className="queue-empty">Activity will appear as you use JARVIS.</div>}</section>
      </section>}

      {page === 'showcase' && <section className="page showcase-page"><PageHeader kicker="ENGINEERING CASE STUDY" title="Built as a career operating system." copy="A production-deployed, approval-gated intelligence product—not a static dashboard." action={<a className="primary" href="https://github.com/syedsaud15" target="_blank" rel="noreferrer">GitHub profile ↗</a>}/><div className="showcase-grid"><article><span>01 · DISCOVER</span><h2>Market intelligence</h2><p>Live job discovery, explainable ranking, quality scoring, deduplication and India-wide filters.</p></article><article><span>02 · DECIDE</span><h2>Career copilot</h2><p>Resume evidence, skill gaps, tailored applications and role-specific interview preparation.</p></article><article><span>03 · EXECUTE</span><h2>Human-in-the-loop automation</h2><p>Every external Gmail or Calendar action requires explicit approval and creates an audit record.</p></article><article><span>04 · OPERATE</span><h2>Production engineering</h2><p>FastAPI, React, PostgreSQL, Docker, CI, OAuth, health checks, validation and secure deployment.</p></article></div><section className="architecture"><p>Source repository is private. This public case study demonstrates the architecture and workflows; the GitHub link opens the creator’s profile.</p><span>REFERENCE ARCHITECTURE</span><div><b>React experience</b><i>→</i><b>NGINX security edge</b><i>→</i><b>FastAPI services</b><i>→</i><b>Neon PostgreSQL</b></div><small>External providers: Adzuna · Google OAuth · Gmail · Calendar</small></section></section>}

      {page === 'privacy' && <section className="page legal-page"><PageHeader kicker="TRUST CENTER" title="Private by architecture." copy="Clear boundaries between the public product experience and the owner's real workspace."/><div className="legal-grid"><article><h2>Public demo</h2><p>Uses synthetic sample data. It does not upload files, call private APIs, send email, create events or store visitor information.</p></article><article><h2>Personal workspace</h2><p>Protected by authentication. Google actions are approval-gated; OAuth tokens are encrypted before database storage.</p></article><article><h2>Data minimization</h2><p>Resume content is used only for career matching. Secrets never ship to the browser or source repository.</p></article><article><h2>Disclaimer</h2><p>Job availability, salaries and fit scores are informational signals—not employment guarantees. Verify every listing before applying.</p></article></div><p className="legal-note">Portfolio demonstration by Syed Saud · JARVIS Career OS · No affiliation with Marvel, Iron Man or third-party job platforms.</p></section>}
    </main>
  </div>
}

export default App

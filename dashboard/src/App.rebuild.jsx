import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import './App.rebuild.css'
import reactorImage from './assets/jarvis-reactor.png'

const stages = ['SAVED', 'APPLIED', 'INTERVIEW', 'REJECTED']
const navItems = [
  ['overview', '⌂', 'Overview'],
  ['opportunities', '◇', 'Opportunities'],
  ['pipeline', '▥', 'Pipeline'],
  ['actions', '↗', 'Action center'],
  ['insights', '◎', 'Insights & settings'],
]

function PageHeader({ kicker, title, copy, action }) {
  return <header className="page-heading"><div><span>{kicker}</span><h1>{title}</h1><p>{copy}</p></div>{action}</header>
}

function formatTimestamp(value) {
  if (!value) return '—'
  const parsed = new Date(value)
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
  const [busy, setBusy] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [apiOnline, setApiOnline] = useState(true)
  const [lastSynced, setLastSynced] = useState(null)
  const [decisionBusy, setDecisionBusy] = useState(null)
  const [notice, setNotice] = useState('All systems operational')
  const scanInputRef = useRef(null)

  const saved = useMemo(() => new Set(applications.map((item) => item.job_listing_id)), [applications])
  const averageFit = jobs.length ? Math.round(jobs.reduce((sum, job) => sum + job.match_score, 0) / jobs.length) : 0
  const pipeline = useMemo(() => Object.fromEntries(stages.map((stage) => [stage, applications.filter((item) => item.status === stage)])), [applications])
  const signals = useMemo(() => Object.entries(jobs.flatMap((job) => job.matched_skills || []).reduce((all, skill) => ({ ...all, [skill]: (all[skill] || 0) + 1 }), {})).sort((a, b) => b[1] - a[1]).slice(0, 6), [jobs])
  const visibleJobs = useMemo(() => jobs.filter((job) => jobFilter === 'high' ? job.match_score >= 50 : jobFilter === 'mnc' ? job.mnc_priority : true).sort((a, b) => b.match_score - a.match_score), [jobs, jobFilter])
  const greeting = useMemo(() => { const hour = new Date().getHours(); return hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening' }, [])

  const loadData = useCallback(async (showStatus = false) => {
    setSyncing(true)
    if (showStatus) setNotice('Synchronizing career intelligence…')
    try {
      const urls = ['/api/jobs?limit=15', '/api/applications', '/api/profile', '/api/analytics', '/api/integrations', '/api/alerts', '/api/approvals', '/api/notifications', '/api/activity', '/api/settings', '/api/reports/weekly']
      const responses = await Promise.all(urls.map((url) => apiRequest(url, { cache: 'no-store' })))
      const data = await Promise.all(responses.map((response) => response.json()))
      setJobs(data[0]); setApplications(data[1]); setProfile(data[2]); setAnalytics(data[3]); setIntegrations(data[4]); setAlerts(data[5]); setApprovals(data[6]); setNotifications(data[7]); setActivity(data[8]); setSettings(data[9]); setWeekly(data[10])
      setApiOnline(true); setLastSynced(new Date())
      if (showStatus) setNotice('Career intelligence synchronized')
    } catch (error) {
      setApiOnline(false); setNotice(error.name === 'AbortError' ? 'API request timed out' : error.message)
      throw error
    } finally { setSyncing(false) }
  }, [])

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

  async function scan(eventObject) {
    eventObject.preventDefault(); if (!query.trim() || busy) return
    setBusy(true); setNotice('Scanning live market signals…')
    try {
      await apiRequest('/api/process', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message: query, sender: 'dashboard-user' }) }, 90000)
      await loadData(); setNotice('Opportunity map updated'); setPage('opportunities')
    } catch (error) { setNotice(error.message || 'Scan interrupted — check backend') } finally { setBusy(false) }
  }
  async function saveJob(id) { const response = await fetch('/api/applications', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ job_listing_id: id, sender: 'dashboard-user' }) }); if (response.ok) await loadData() }
  async function moveApplication(id, status) { const response = await fetch(`/api/applications/${id}/status`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) }); if (response.ok) await loadData() }
  async function uploadResume(e) { const file = e.target.files?.[0]; if (!file) return; const body = new FormData(); body.append('file', file); setNotice('Analyzing resume…'); const response = await fetch('/api/profile/upload', { method: 'POST', body }); if (response.ok) { await loadData(); setNotice('Resume intelligence updated') } else setNotice('Resume upload failed') }
  async function connectGoogle() { const response = await fetch('/api/integrations/google/start'); const result = await response.json().catch(() => ({})); if (response.ok) window.location.assign(result.authorization_url); else setNotice(result.detail || 'Google connection failed') }
  async function requestEmail(e) { e.preventDefault(); const response = await fetch('/api/actions/email/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(email) }); if (response.ok) { setEmail({ to: '', subject: '', body: '' }); await loadData(); setNotice('Email queued for approval') } }
  async function requestEvent(e) { e.preventDefault(); if (new Date(event.ends_at) <= new Date(event.starts_at)) { setNotice('End time must be after start time'); return } const response = await fetch('/api/actions/calendar/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(event) }); if (response.ok) { setEvent({ title: '', starts_at: '', ends_at: '' }); await loadData(); setNotice('Calendar event queued for approval') } }
  async function decide(id, decision) { setDecisionBusy(id); try { const response = await apiRequest(`/api/approvals/${id}/decision`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ decision }) }, 60000); const result = await response.json().catch(() => ({})); setNotice(result.execution || `Action ${decision.toLowerCase()}`); await loadData() } catch (error) { setNotice(error.message) } finally { setDecisionBusy(null) } }
  async function openWorkspace(item) { setSelected(item); setPage('pipeline'); const [notesResponse, draftResponse, prepResponse] = await Promise.all([fetch(`/api/applications/${item.id}/notes`), fetch(`/api/applications/${item.id}/cover-letter`), fetch(`/api/applications/${item.id}/interview-prep`)]); if (notesResponse.ok) setNotes(await notesResponse.json()); if (draftResponse.ok) setCoverLetter((await draftResponse.json()).draft); if (prepResponse.ok) setInterviewPrep(await prepResponse.json()) }
  async function addNote(e) { e.preventDefault(); if (!selected || !note.trim()) return; const response = await fetch(`/api/applications/${selected.id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ body: note }) }); if (response.ok) { setNotes([await response.json(), ...notes]); setNote('') } }
  async function scheduleFollowUp(e) { e.preventDefault(); if (!selected || !followUp) return; const response = await fetch(`/api/applications/${selected.id}/follow-ups`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ due_on: followUp }) }); if (response.ok) { setFollowUp(''); await loadData(); setNotice('Follow-up scheduled') } }
  async function saveSettings(e) { e.preventDefault(); try { const response = await apiRequest('/api/settings', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(settings) }); setSettings(await response.json()); setNotice('Career preferences saved') } catch (error) { setNotice(error.message) } }

  return <div className="jarvis-app">
    <aside className="side-rail">
      <button className="brand" onClick={() => setPage('overview')}><b>J</b><span>JARVIS<small>CAREER INTELLIGENCE</small></span></button>
      <nav>{navItems.map(([id, icon, label]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => setPage(id)}><i>{icon}</i><span>{label}</span>{id === 'actions' && approvals.length > 0 && <em>{approvals.length}</em>}</button>)}</nav>
      <div className="rail-card"><span>PROFILE ENGINE</span><strong>{profile.resume_connected ? 'Resume online' : 'Resume needed'}</strong><small>{profile.skills?.length || 0} skills mapped</small><label>{profile.resume_connected ? 'Update resume' : 'Add resume'}<input type="file" accept=".pdf,.txt" onChange={uploadResume} /></label></div>
      <footer><span className="avatar">SS</span><div><b>Syed Saud</b><small>Data Engineer</small></div><i>•••</i></footer>
    </aside>

    <main className="product-area">
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
      <div className="topbar"><div className={`status-pill ${apiOnline ? '' : 'offline'}`} role="status" aria-live="polite"><i />{notice}{lastSynced && <small> · {lastSynced.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</small>}</div><div className="top-actions">{notifications.length > 0 && <button type="button" onClick={() => setPage('insights')}>Alerts {notifications.length}</button>}<button type="button" disabled={syncing} onClick={() => void loadData(true)}>{syncing ? 'Syncing…' : 'Sync data'}</button><button type="button" className="command-key" aria-label="Focus intelligence scan" onClick={() => { setPage('overview'); window.setTimeout(() => scanInputRef.current?.focus(), 0) }}>⌘ K</button></div></div>

      {page === 'overview' && <section className="page overview-page">
        <PageHeader kicker="CAREER COMMAND CENTER" title={<>{greeting}, Syed.<br/><em>Your next move is getting clearer.</em></>} copy="A live operating picture of your market, profile and active opportunities." action={<div className="system-orb reactor-image-mark" aria-label="JARVIS intelligence reactor online"><img src={reactorImage} alt="" /><i><span />JARVIS INTELLIGENCE</i></div>} />
        <form className="scan-bar" onSubmit={scan}><span aria-hidden="true">⌕</span><label className="sr-only" htmlFor="career-scan">Career intelligence query</label><input id="career-scan" ref={scanInputRef} value={query} onChange={(e) => setQuery(e.target.value)} autoComplete="off" /><button disabled={busy}>{busy ? 'Scanning market…' : 'Run intelligence scan'} ↗</button></form>
        <div className="metric-grid"><article><span>Market signals</span><strong>{jobs.length}</strong><small>{profile.skills?.length || 0} profile skills mapped</small></article><article><span>Average fit</span><strong>{averageFit || '—'}{averageFit ? '%' : ''}</strong><small>Across live roles</small></article><article><span>Active pipeline</span><strong>{applications.length}</strong><small>{analytics.interview_rate}% interview rate</small></article><article><span>Pending actions</span><strong>{approvals.length}</strong><small>Approval protected</small></article></div>
        <div className="overview-grid">
          <section className="panel market-panel"><header><div><span>MARKET PULSE</span><h2>Skills creating leverage</h2></div><button onClick={() => setPage('opportunities')}>Explore roles ↗</button></header><div className="signal-chart">{signals.map(([skill, count], index) => <div key={skill}><span>0{index + 1}</span><b>{skill}</b><i><u style={{width:`${Math.min(100, 35 + count * 13)}%`}} /></i><em>{count} signals</em></div>)}</div></section>
          <section className="panel radar-panel"><header><span>HIGH-FIT RADAR</span><b>{alerts.length} LIVE</b></header>{alerts.slice(0, 3).map((alert) => <article key={`${alert.title}-${alert.company}`}><div className="score-ring">{alert.match_score}%</div><div><strong>{alert.title}</strong><small>{alert.company}</small></div></article>)}{!alerts.length && <div className="panel-empty">Run a scan to activate your radar.</div>}</section>
        </div>
        <section className="panel integration-panel"><div><span>CONNECTED WORKSPACE</span><h2>Your career stack, synchronized.</h2></div><div className="integration-row">{integrations.map((item) => <div key={item.name} className={item.status === 'CONNECTED' ? 'online' : ''}><i>{item.name.includes('Gmail') ? 'M' : item.name.includes('Calendar') ? '31' : 'A'}</i><span><b>{item.name}</b><small>{item.status === 'CONNECTED' ? 'Connected' : 'Ready to connect'}</small></span></div>)}{integrations.some((item) => item.status === 'OAUTH_REQUIRED') && <button onClick={connectGoogle}>Connect Google</button>}</div></section>
      </section>}

      {page === 'opportunities' && <section className="page">
        <PageHeader kicker="OPPORTUNITY INTELLIGENCE" title="Roles worth your attention." copy="Ranked by evidence from your resume, market demand and employer quality." action={<button className="primary" onClick={() => setPage('overview')}>New scan ↗</button>} />
        <div className="filter-row"><button className={jobFilter === 'all' ? 'active' : ''} onClick={() => setJobFilter('all')}>All signals <b>{jobs.length}</b></button><button className={jobFilter === 'high' ? 'active' : ''} onClick={() => setJobFilter('high')}>High fit</button><button className={jobFilter === 'mnc' ? 'active' : ''} onClick={() => setJobFilter('mnc')}>MNC priority</button><span>{visibleJobs.length} roles · sorted by profile fit</span></div>
        <div className="job-grid">{visibleJobs.map((job) => <article key={job.id} className="job-card"><header><div className="company-mark">{(job.company || 'J').charAt(0)}</div><div className="match"><strong>{job.match_score}%</strong><small>PROFILE FIT</small></div></header><span className="location">{job.location || 'Location flexible'}</span><h2>{job.title}</h2><p>{job.company || 'Employer signal'}</p><div className="chip-row">{(job.matched_skills || []).slice(0,4).map((skill) => <span key={skill}>{skill}</span>)}</div><small className="explain">{job.match_explanation}</small><footer>{job.redirect_url && <a href={job.redirect_url} target="_blank" rel="noreferrer">View role ↗</a>}<button disabled={saved.has(job.id)} onClick={() => saveJob(job.id)}>{saved.has(job.id) ? 'Captured ✓' : 'Capture role'}</button></footer></article>)}</div>
        {!visibleJobs.length && <div className="results-empty"><b>No matching roles in this view.</b><span>Try another filter or run a fresh intelligence scan.</span><button onClick={() => setJobFilter('all')}>Show all opportunities</button></div>}
      </section>}

      {page === 'pipeline' && <section className="page">
        <PageHeader kicker="APPLICATION PIPELINE" title="Every opportunity, in motion." copy="Move roles forward and keep the next action visible." action={<a className="primary" href="/api/applications/export.csv">Export CSV ↗</a>} />
        <div className="pipeline-board">{stages.map((stage) => <section key={stage}><header><span>{stage}</span><b>{pipeline[stage].length}</b></header>{pipeline[stage].map((item) => <article key={item.id}><strong>{item.title}</strong><small>{item.company}</small><button onClick={() => openWorkspace(item)}>Open workspace</button>{stage === 'SAVED' && <button onClick={() => moveApplication(item.id, 'APPLIED')}>Mark applied →</button>}{stage === 'APPLIED' && <button onClick={() => moveApplication(item.id, 'INTERVIEW')}>Move to interview →</button>}</article>)}{!pipeline[stage].length && <div className="drop-zone">No roles yet</div>}</section>)}</div>
        {selected && <section className="detail-drawer"><header><div><span>APPLICATION WORKSPACE</span><h2>{selected.title}</h2><p>{selected.company}</p></div><button onClick={() => setSelected(null)}>×</button></header><div className="detail-grid"><div><form onSubmit={addNote}><label>Private note<textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Recruiter details, interview notes, next move…" /></label><button>Add note</button></form><div className="notes-list">{notes.map((item) => <p key={item.id}>{item.body}</p>)}</div><form className="follow-form" onSubmit={scheduleFollowUp}><input type="date" value={followUp} onChange={(e) => setFollowUp(e.target.value)} /><button>Schedule follow-up</button></form></div><div className="draft"><span>TAILORED COVER LETTER</span><pre>{coverLetter}</pre>{interviewPrep && <div className="prep-block"><span>INTERVIEW INTELLIGENCE</span><b>Strengths: {interviewPrep.matched_strengths.join(', ') || 'Build evidence from your projects'}</b><small>Gaps: {interviewPrep.skill_gaps.join(', ') || 'No critical skill gap detected'}</small>{interviewPrep.questions.slice(0,3).map((question) => <p key={question}>{question}</p>)}</div>}</div></div></section>}
      </section>}

      {page === 'actions' && <section className="page">
        <PageHeader kicker="APPROVAL-GATED AUTOMATION" title="You stay in control." copy="JARVIS prepares the work. Nothing is sent or scheduled without your approval." />
        <div className="action-grid"><form className="composer" onSubmit={requestEmail}><span>GMAIL COMPOSER</span><h2>Draft an outreach email</h2><input type="email" placeholder="Recipient email" value={email.to} onChange={(e) => setEmail({...email,to:e.target.value})} required/><input placeholder="Subject" value={email.subject} onChange={(e) => setEmail({...email,subject:e.target.value})} required/><textarea placeholder="Write your message…" value={email.body} onChange={(e) => setEmail({...email,body:e.target.value})} required/><button>Send for approval ↗</button></form><form className="composer" onSubmit={requestEvent}><span>CALENDAR COMPOSER</span><h2>Schedule an interview</h2><input placeholder="Event title" value={event.title} onChange={(e) => setEvent({...event,title:e.target.value})} required/><label>Starts<input type="datetime-local" value={event.starts_at} onChange={(e) => setEvent({...event,starts_at:e.target.value})} required/></label><label>Ends<input type="datetime-local" value={event.ends_at} onChange={(e) => setEvent({...event,ends_at:e.target.value})} required/></label><button>Send for approval ↗</button></form></div>
        <section className="approval-queue"><header><div><span>APPROVAL QUEUE</span><h2>Ready for your decision</h2></div><b>{approvals.length} pending</b></header>{approvals.map((item) => <article key={item.id}><div><i>↗</i><span><strong>{item.summary}</strong><small>{item.tool_name}</small></span></div><footer><button disabled={decisionBusy === item.id} onClick={() => decide(item.id,'REJECTED')}>Reject</button><button disabled={decisionBusy === item.id} onClick={() => decide(item.id,'APPROVED')}>{decisionBusy === item.id ? 'Executing…' : 'Approve & execute'}</button></footer></article>)}{!approvals.length && <div className="queue-empty">Everything is clear. No actions waiting.</div>}</section>
      </section>}

      {page === 'insights' && <section className="page">
        <PageHeader kicker="CAREER OPERATIONS" title="Your intelligence layer." copy="Preferences, reminders, weekly performance and a traceable activity history." />
        <div className="insight-grid">
          <form className="composer settings-form" onSubmit={saveSettings}><span>CAREER PREFERENCES</span><h2>Calibrate JARVIS</h2><input value={settings.display_name} onChange={(e) => setSettings({...settings, display_name:e.target.value})} placeholder="Display name" required/><input value={settings.target_role} onChange={(e) => setSettings({...settings, target_role:e.target.value})} placeholder="Target role" required/><input value={settings.target_location} onChange={(e) => setSettings({...settings, target_location:e.target.value})} placeholder="Target location" required/><label>Minimum profile fit<input type="number" min="0" max="100" value={settings.minimum_fit} onChange={(e) => setSettings({...settings, minimum_fit:Number(e.target.value)})}/></label><label className="check"><input type="checkbox" checked={settings.weekly_digest} onChange={(e) => setSettings({...settings, weekly_digest:e.target.checked})}/> Weekly intelligence digest</label><label className="check"><input type="checkbox" checked={settings.follow_up_reminders} onChange={(e) => setSettings({...settings, follow_up_reminders:e.target.checked})}/> Follow-up reminders</label><button>Save preferences ↗</button></form>
          <section className="panel weekly-panel"><header><div><span>WEEKLY COMMAND BRIEF</span><h2>Momentum at a glance</h2></div></header>{weekly && <div className="weekly-stats"><article><strong>{weekly.new_applications}</strong><small>NEW APPLICATIONS</small></article><article><strong>{weekly.interviews_moved}</strong><small>INTERVIEWS</small></article><article><strong>{weekly.interview_rate}%</strong><small>INTERVIEW RATE</small></article><p>{weekly.recommended_focus}</p></div>}<div className="notification-list">{notifications.map((item) => <article key={item.id}><b>{item.title}</b><small>{item.detail}</small></article>)}{!notifications.length && <p>All clear. No reminders need attention.</p>}</div></section>
        </div>
        <section className="approval-queue activity-log"><header><div><span>AUDIT & ACTIVITY</span><h2>Everything JARVIS has touched</h2></div><b>{activity.length} events</b></header>{activity.slice(0,20).map((item, index) => <article key={`${item.created_at}-${index}`}><div><i>◎</i><span><strong>{item.type.replaceAll('.', ' ')}</strong><small>{item.details}</small></span></div><time>{formatTimestamp(item.created_at)}</time></article>)}{!activity.length && <div className="queue-empty">Activity will appear as you use JARVIS.</div>}</section>
      </section>}
    </main>
  </div>
}

export default App

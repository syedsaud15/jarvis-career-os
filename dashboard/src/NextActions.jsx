export default function NextActions({ applications, approvals, followUps, isDemo, onPage, onWorkspace }) {
  const today = new Date().toISOString().slice(0, 10)
  const items = []
  for (const follow of [...followUps].sort((a, b) => String(a.due_on).localeCompare(String(b.due_on)))) {
    if (!follow.due_on || String(follow.due_on).slice(0, 10) > today) continue
    const application = applications.find(item => item.id === follow.application_id)
    items.push({ key: `follow-${follow.id}`, label: 'FOLLOW-UP DUE', title: follow.title || 'Review your follow-up', detail: `${follow.company || 'Application'} · ${String(follow.due_on).slice(0, 10)} UTC`, run: () => application ? onWorkspace(application) : onPage('insights') })
  }
  if (approvals.length) items.push({ key: 'approvals', label: 'YOUR DECISION', title: `${approvals.length} pending approval${approvals.length === 1 ? '' : 's'}`, detail: 'Review details before any external action.', run: () => onPage('actions') })
  const saved = applications.find(item => item.status === 'SAVED')
  if (saved) items.push({ key: 'saved', label: 'PREPARE APPLICATION', title: saved.title, detail: `${saved.company || 'Saved role'} · Open copilot and interview prep`, run: () => onWorkspace(saved) })
  return <section className="panel next-actions" aria-labelledby="next-actions-title">
    <header><div><span>{isDemo ? 'SAMPLE NEXT STEPS' : 'FOCUS QUEUE'}</span><h2 id="next-actions-title">Your next actions</h2></div><span className="next-count">{Math.min(items.length, 3)}</span></header>
    <div className="next-actions-body">{items.length ? items.slice(0, 3).map(item => <button key={item.key} onClick={item.run}><span><small>{item.label}</small><strong>{item.title}</strong><em>{item.detail}</em></span><span aria-hidden="true">↗</span></button>) : <div className="next-empty"><strong>No pending actions</strong><p>{applications.length ? 'Your queue is clear. Explore opportunities when you are ready.' : 'Capture your first role to start preparing an application.'}</p><button onClick={() => onPage('opportunities')}>Explore opportunities ↗</button></div>}<p className="next-note">{isDemo ? 'Sample workspace · ' : ''}Shortcuts only—nothing is sent or changed automatically.</p></div>
  </section>
}

export default function CareerActivity({ trends, isDemo, onDetails }) {
  const weeks = trends?.weeks || []
  const current = weeks.at(-1)
  const maximum = Math.max(1, ...weeks.map((week) => week.captured))
  const points = weeks.map((week, index) => `${16 + index * 368 / Math.max(1, weeks.length - 1)},${102 - week.captured / maximum * 80}`).join(' ')
  return <section className="panel career-activity" aria-labelledby="career-activity-title">
    <header><div><span>{isDemo ? 'SAMPLE ACTIVITY' : 'CAREER ACTIVITY'} · UTC</span><h2 id="career-activity-title">Your weekly momentum</h2></div><button onClick={onDetails} aria-label="View detailed activity trends">↗</button></header>
    <div className="activity-body"><div className="activity-summary"><div><strong className="activity-total">{current?.captured ?? '—'}</strong><span> saved this week</span></div><span className="activity-badge">8-week view</span></div>
      {weeks.length ? <svg viewBox="0 0 400 120" role="img" aria-label={`Weekly captured roles, oldest to newest: ${weeks.map((week) => `${week.week_start}: ${week.captured}`).join('; ')}`}><path d="M16 102H384" stroke="#b9c9cf" fill="none"/><polygon points={`16,102 ${points} 384,102`} fill="#efad5220"/><polyline points={points} fill="none" stroke="#ae5a13" strokeWidth="3" strokeLinejoin="round"/>{weeks.map((week, index) => <circle key={week.week_start} cx={16 + index * 368 / Math.max(1, weeks.length - 1)} cy={102 - week.captured / maximum * 80} r="4" fill="#ae5a13"/>)}</svg> : <p>Activity history is not available yet.</p>}
      <div className="activity-caption"><span>{weeks.some(week => week.captured > 0) ? 'Weekly saved roles' : 'Capture a role to start your trend'}</span><span>UTC</span></div>
      <dl><div><dt>Applied moves</dt><dd>{current?.applied ?? '—'}</dd></div><div><dt>Interview moves</dt><dd>{current?.interviews ?? '—'}</dd></div></dl>
      <p>{isDemo ? 'Sample data · ' : ''}This week so far · saved roles, not submissions.</p>
    </div>
  </section>
}

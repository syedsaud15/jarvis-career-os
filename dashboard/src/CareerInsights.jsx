export default function CareerInsights({ roadmap, trends, isDemo, onUploadResume }) {
  return <div className="completion-insights">
    <section className="panel roadmap-panel" aria-labelledby="roadmap-title">
      <header><div><span>SKILL-GAP ROADMAP</span><h2 id="roadmap-title">Your next learning priorities</h2></div></header>
      <div className="insight-content"><p>Based on missing skills across recent cached roles. Practice first; only claim skills backed by real work.</p>
        {!isDemo && <button className="primary" onClick={onUploadResume}>Upload or update resume</button>}
        {roadmap?.roadmap?.length ? <ol>{roadmap.roadmap.map((item) => <li key={item.skill}><h3>{item.skill} · {item.demand_signals} role signals</h3><p>{item.project}</p><small>Evidence checkpoint: explain your design, test failure cases and publish a measured result.</small></li>)}</ol> : <p>Upload your resume and scan jobs to identify learning priorities.</p>}
      </div>
    </section>
    <section className="panel trends-panel" aria-labelledby="trends-title">
      <header><div><span>WEEKLY HISTORY · UTC</span><h2 id="trends-title">Eight-week activity trends</h2></div></header>
      <div className="insight-content"><p>{isDemo ? 'Illustrative sample history, not real activity.' : trends?.coverage_note}</p><p>Current week is partial. Captures are saved roles, not submitted applications. The funnel above is a current-stage snapshot. Interview rate compares current interviews with current applied + interview roles; it is not a historical success rate.</p>
        <div className="table-scroll" tabIndex={0} role="region" aria-label="Weekly activity table"><table><caption>Weekly captures and recorded stage changes</caption><thead><tr><th scope="col">Week starting</th><th scope="col">Captured</th><th scope="col">Applied</th><th scope="col">Interview</th><th scope="col">Rejected</th></tr></thead><tbody>{trends?.weeks?.map((week) => <tr key={week.week_start}><th scope="row">{week.week_start}</th><td>{week.captured}</td><td>{week.applied}</td><td>{week.interviews}</td><td>{week.rejected}</td></tr>)}</tbody></table></div>
      </div>
    </section>
    {!isDemo && <section className="panel backup-panel"><div className="insight-content"><h2>Private career-data backup</h2><p>Includes captured roles, resume, preferences, notes, follow-ups and tracked stage history. Excludes passwords, Google tokens, pending actions and uncaptured job cache. Keep the downloaded file private.</p><a className="primary" href="/api/backup/export.json">Download career backup</a></div></section>}
  </div>
}

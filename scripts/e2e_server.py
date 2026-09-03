"""Local-only synthetic browser-test server. Never uses the configured database."""
from dataclasses import replace
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app import main
from app.store import Store
from app.orchestrator import Orchestrator
from app.approvals import ApprovalService

root = Path(__file__).resolve().parents[1]
test_dir = root / '.qa' / uuid4().hex
test_dir.mkdir(parents=True)
main.settings = replace(main.settings, database_url=None, database_path=test_dir / 'e2e.db', api_key=None,
                        adzuna_app_id=None, adzuna_app_key=None, google_client_id=None,
                        google_client_secret=None, groq_api_key=None)
main.store = Store(main.settings.database_path)
main.store.initialize()
main.orchestrator = Orchestrator(main.store, main.settings)
main.approvals = ApprovalService(main.store)
with main.store.connection() as con:
    con.execute("INSERT INTO job_listings(source,source_id,query,title,company,location,description,salary_min,salary_max,posted_at) VALUES('fixture','1','data','Data Engineer','QA Example','Remote India','python sql kafka',1500000,2200000,'2030-01-01')")
main.save_profile('dashboard-user', 'Python SQL pipeline experience with tests and measurable reliability')

app = FastAPI()
app.mount('/api', main.app)
app.mount('/assets', StaticFiles(directory=root / 'dashboard/dist/assets'), name='assets')

@app.post('/__test/reset')
def reset_fixture():
    # This route exists only in this loopback test harness, never in app.main.
    main.store = Store(test_dir / f'{uuid4().hex}.db')
    main.store.initialize()
    main.approvals = ApprovalService(main.store)
    main.orchestrator = Orchestrator(main.store, main.settings)
    main.request_window.clear()
    with main.store.connection() as con:
        con.execute("INSERT INTO job_listings(source,source_id,query,title,company,location,description,salary_min,salary_max,posted_at) VALUES('fixture','1','data','Data Engineer','QA Example','Remote India','python sql kafka',1500000,2200000,?)", (datetime.now(timezone.utc).isoformat(),))
    main.save_profile('dashboard-user', 'Python SQL pipeline experience with tests and measurable reliability')
    return {'status': 'reset'}

@app.get('/{path:path}')
def frontend(path: str, request: Request):
    if path == '__test/axe.js':
        return FileResponse(root / 'dashboard/node_modules/axe-core/axe.min.js')
    if path == '__test/audit.js':
        return FileResponse(root / 'scripts/e2e_audit.js')
    if request.query_params.get('qa-a11y') == '1':
        html = (root / 'dashboard/dist/index.html').read_text(encoding='utf-8')
        return HTMLResponse(html.replace('</body>', '<script src="/__test/axe.js"></script><script src="/__test/audit.js"></script></body>'))
    return FileResponse(root / 'dashboard/dist/index.html')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=4173)

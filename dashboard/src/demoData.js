const now = new Date()
const isoDaysAgo = (days) => new Date(now.getTime() - days * 86400000).toISOString()
const monday = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - (now.getUTCDay() + 6) % 7))

export const demoJobs = [
  { id: 9001, title: 'Senior Data Engineer', company: 'Nimbus Analytics', location: 'Bengaluru, Karnataka', description: 'Build Python, SQL, Spark and Databricks pipelines on AWS.', salary_min: 1800000, salary_max: 2600000, posted_at: isoDaysAgo(2), redirect_url: '#demo-role', match_score: 86, quality_score: 92, matched_skills: ['python','sql','spark','databricks'], missing_skills: ['kafka'], mnc_priority: true, work_mode: 'HYBRID', experience_level: 'SENIOR', age_days: 2, is_expired: false, match_explanation: 'Strong skill alignment, fresh listing and high-quality employer signal.', next_step: 'Lead with your production pipeline reliability metrics.' },
  { id: 9002, title: 'Data Platform Engineer', company: 'Atlas Financial', location: 'Pune, Maharashtra', description: 'Own Airflow, dbt, Snowflake and Python data products.', salary_min: 1500000, salary_max: 2200000, posted_at: isoDaysAgo(4), redirect_url: '#demo-role', match_score: 78, quality_score: 88, matched_skills: ['python','airflow','dbt','snowflake'], missing_skills: ['gcp'], mnc_priority: true, work_mode: 'HYBRID', experience_level: 'MID', age_days: 4, is_expired: false, match_explanation: 'Excellent platform-tool overlap with a verified enterprise employer.', next_step: 'Showcase orchestration and data-quality ownership.' },
  { id: 9003, title: 'Data Engineer II', company: 'Orbit Commerce', location: 'Remote, India', description: 'Remote role using SQL, AWS, Kafka and Docker.', salary_min: 1400000, salary_max: 2000000, posted_at: isoDaysAgo(1), redirect_url: '#demo-role', match_score: 73, quality_score: 84, matched_skills: ['sql','aws','docker'], missing_skills: ['kafka'], mnc_priority: false, work_mode: 'REMOTE', experience_level: 'MID', age_days: 1, is_expired: false, match_explanation: 'Fresh remote role with strong cloud and SQL evidence.', next_step: 'Add one Kafka delivery example to your application.' },
  { id: 9004, title: 'Azure Data Engineer', company: 'Vertex Systems', location: 'Hyderabad, Telangana', description: 'Develop Azure, Databricks, PySpark and ETL workloads.', salary_min: 1200000, salary_max: 1900000, posted_at: isoDaysAgo(7), redirect_url: '#demo-role', match_score: 69, quality_score: 80, matched_skills: ['azure','databricks','pyspark','etl'], missing_skills: [], mnc_priority: false, work_mode: 'ONSITE', experience_level: 'MID', age_days: 7, is_expired: false, match_explanation: 'Focused Azure stack match with transparent role requirements.', next_step: 'Quantify Databricks performance improvements.' },
  { id: 9005, title: 'Analytics Engineer', company: 'Lakehouse Labs', location: 'Gurugram, Haryana', description: 'Model trusted datasets with SQL, dbt and Snowflake.', salary_min: 1000000, salary_max: 1600000, posted_at: isoDaysAgo(12), redirect_url: '#demo-role', match_score: 61, quality_score: 76, matched_skills: ['sql','dbt','snowflake'], missing_skills: [], mnc_priority: false, work_mode: 'HYBRID', experience_level: 'MID', age_days: 12, is_expired: false, match_explanation: 'Good modelling fit with a complete salary signal.', next_step: 'Emphasize stakeholder-facing data modelling.' },
  { id: 9006, title: 'Associate Data Engineer', company: 'Pulse Mobility', location: 'Chennai, Tamil Nadu', description: 'Entry role covering Python, SQL and ETL foundations.', salary_min: 700000, salary_max: 1100000, posted_at: isoDaysAgo(5), redirect_url: '#demo-role', match_score: 57, quality_score: 72, matched_skills: ['python','sql','etl'], missing_skills: ['spark'], mnc_priority: false, work_mode: 'ONSITE', experience_level: 'ENTRY', age_days: 5, is_expired: false, match_explanation: 'Solid foundation match with clear experience expectations.', next_step: 'Position your project work as production-ready evidence.' },
]

export const demoApplications = [
  { id: 8001, job_listing_id: 9002, title: 'Data Platform Engineer', company: 'Atlas Financial', status: 'INTERVIEW', location: 'Pune, Maharashtra' },
  { id: 8002, job_listing_id: 9003, title: 'Data Engineer II', company: 'Orbit Commerce', status: 'APPLIED', location: 'Remote, India' },
  { id: 8003, job_listing_id: 9004, title: 'Azure Data Engineer', company: 'Vertex Systems', status: 'SAVED', location: 'Hyderabad, Telangana' },
]

export const demoData = {
  jobs: demoJobs,
  roadmap: { roadmap: [{ skill: 'kafka', demand_signals: 2, project: 'Build a local event pipeline with retries, consumer lag monitoring and integration tests.' }, { skill: 'gcp', demand_signals: 1, project: 'Design and document a warehouse pipeline; validate the transformations locally without paid cloud resources.' }] },
  trends: { weeks: Array.from({length: 8}, (_, i) => ({week_start: new Date(monday.getTime() - (7-i)*7*86400000).toISOString().slice(0,10), captured: i === 7 ? 3 : 0, applied: i === 7 ? 2 : 0, interviews: i === 7 ? 1 : 0, rejected: 0})) },
  applications: demoApplications,
  profile: { resume_connected: true, skills: ['python','sql','spark','pyspark','airflow','aws','azure','databricks','snowflake','dbt','docker','etl'] },
  analytics: { interview_rate: 50, open_follow_ups: [{ id: 1, title: 'Data Platform Engineer', company: 'Atlas Financial', due_on: isoDaysAgo(-1).slice(0,10) }] },
  integrations: [
    { name: 'Adzuna job data', status: 'DEMO', capability: 'Sample market intelligence' },
    { name: 'Gmail', status: 'SIMULATED', capability: 'No messages are sent in demo mode' },
    { name: 'Google Calendar', status: 'SIMULATED', capability: 'No events are created in demo mode' },
  ],
  alerts: demoJobs.slice(0,3).map(({ title, company, match_score, next_step }) => ({ type: 'HIGH_FIT_ROLE', title, company, match_score, next_step })),
  approvals: [],
  notifications: [{ id: 'demo-followup', type: 'FOLLOW_UP', title: 'Interview follow-up due tomorrow', detail: 'Atlas Financial' }],
  activity: [
    { type: 'application.updated', entity_type: 'application', details: 'INTERVIEW: Data Platform Engineer', created_at: isoDaysAgo(1) },
    { type: 'scan.completed', entity_type: 'jobs', details: '6 quality-controlled roles ranked', created_at: isoDaysAgo(2) },
    { type: 'profile.updated', entity_type: 'profile', details: '12 skills mapped from resume', created_at: isoDaysAgo(3) },
  ],
  settings: { display_name: 'Demo Candidate', target_role: 'Data Engineer', target_location: 'India', minimum_fit: 45, weekly_digest: true, follow_up_reminders: true },
  weekly: { new_applications: 3, interviews_moved: 1, interview_rate: 50, recommended_focus: 'Prioritize high-quality roles posted in the last seven days.' },
}

from backend.app import create_app, db
from backend.app.models import Report

app = create_app()
with app.app_context():
    reports = Report.query.all()
    print(f'Total reports: {len(reports)}')
    print('Latest reports:')
    for r in reports[-5:]:
        print(f'  {r.id}: {r.title} ({r.format})')

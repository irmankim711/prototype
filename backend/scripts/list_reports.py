from app import create_app
from app.models import Report

app = create_app()

with app.app_context():
    rows = Report.query.filter(Report.file_path != None).order_by(Report.id).all()
    if not rows:
        print('NO_ROWS')
    else:
        for r in rows:
            print(f"{r.id}|{r.file_path}|{r.generation_status}")

from app import create_app

REPORT_ID = 20

app = create_app()
with app.app_context():
    client = app.test_client()
    resp = client.get(f"/api/excel-to-docx/{REPORT_ID}/preview")
    print('STATUS:', resp.status_code)
    print('HEADERS:')
    for k, v in resp.headers.items():
        if k.lower().startswith('x-frame') or k.lower().startswith('content-type') or k.lower().startswith('content-security'):
            print(f"  {k}: {v}")
    try:
        print('\nBODY (JSON):')
        print(resp.get_json())
    except Exception:
        print('\nBODY (TEXT):')
        print(resp.get_data(as_text=True))

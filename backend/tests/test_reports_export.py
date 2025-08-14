import os
import sys
import json
import pytest

# Ensure the backend package path is available for imports
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app, db


@pytest.fixture()
def app_client(tmp_path):
    app = create_app('testing')
    app.config['UPLOAD_FOLDER'] = str(tmp_path / 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        db.create_all()

    client = app.test_client()
    yield client

    with app.app_context():
        db.drop_all()


def test_export_pdf_and_docx_success(app_client):
    payload = {
        'template_id': 'TestTemplate',
        'data_source': {
            'title': 'Integration Export Test',
            'summary': 'This is a test export.'
        },
        'formats': ['pdf', 'docx']
    }
    resp = app_client.post('/api/reports/export', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'urls' in data
    # Confirm URLs exist for requested formats
    assert data['urls']['pdf'] and data['urls']['pdf'].endswith('.pdf')
    assert data['urls']['docx'] and data['urls']['docx'].endswith('.docx')


def test_export_invalid_format_rejected(app_client):
    payload = {
        'template_id': 'TestTemplate',
        'data_source': {},
        'formats': ['exe']
    }
    resp = app_client.post('/api/reports/export', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 400
    body = resp.get_json()
    assert body['status'] == 'error'


def test_export_missing_fields(app_client):
    # Missing template_id
    resp = app_client.post('/api/reports/export', json={'data_source': {}, 'formats': ['pdf']})
    assert resp.status_code == 400

    # Missing data_source
    resp = app_client.post('/api/reports/export', json={'template_id': 'X', 'formats': ['pdf']})
    assert resp.status_code == 400

    # Missing formats
    resp = app_client.post('/api/reports/export', json={'template_id': 'X', 'data_source': {}})
    assert resp.status_code == 400


def test_download_generated_file(app_client):
    payload = {
        'template_id': 'TestTemplate',
        'data_source': {'title': 'Download Test'},
        'formats': ['pdf']
    }
    resp = app_client.post('/api/reports/export', json=payload)
    assert resp.status_code == 200
    body = resp.get_json()
    pdf_url = body['urls']['pdf']
    # fetch file
    download_resp = app_client.get(pdf_url)
    assert download_resp.status_code == 200
    assert download_resp.mimetype == 'application/pdf'

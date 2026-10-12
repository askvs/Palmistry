import sys
sys.path.insert(0, 'backend')
from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())
with open('dataset/palmline/dataset_seimbang/images/test/air_lmars_byk_sh_merq_tsat_a_001.jpg', 'rb') as f:
    response = client.post('/api/v1/palm/analyze', files={'file': ('test.jpg', f, 'image/jpeg')})
print("STATUS:", response.status_code)
print("BODY:", response.text[:2000])

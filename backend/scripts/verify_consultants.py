import sys
sys.path.append('backend')
import urllib.request, json
from app.auth.tokens import create_access_token
from app.db.session import get_db
from app.models.user import User

db = next(get_db())
seeker = db.query(User).filter_by(email='user@palmistry.example.com').first()
consultant = db.query(User).filter_by(email='consultant@palmistry.example.com').first()
reader = db.query(User).filter_by(email='reader@palmistry.example.com').first()
admin = db.query(User).filter_by(email='admin@palmistry.example.com').first()

s_tok = create_access_token(seeker.id, role=seeker.role)
c_tok = create_access_token(consultant.id, role=consultant.role)
r_tok = create_access_token(reader.id, role=reader.role)
a_tok = create_access_token(admin.id, role=admin.role)

def test_get(url, token, desc):
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req, timeout=15) as r:
        assert r.status == 200
        print(f'PASS [200]: {desc}')
        return json.loads(r.read())

d = test_get('http://127.0.0.1:8000/api/v1/consultants', s_tok, 'Seeker opens Find a Consultant')
assert len(d['items']) >= 3
cid = d['items'][0]['id']

tf = test_get('http://127.0.0.1:8000/api/v1/consultants?specialization=tarot', s_tok, 'Filter by tarot specialization')
assert len(tf['items']) >= 1

det = test_get(f'http://127.0.0.1:8000/api/v1/consultants/{cid}', s_tok, 'Consultant Profile detail')

av = test_get(f'http://127.0.0.1:8000/api/v1/consultants/{cid}/availability', s_tok, 'Consultant Availability strip')
assert len(av['days']) > 0

test_get('http://127.0.0.1:8000/api/v1/bookings', s_tok, 'Seeker My Sessions')

test_get('http://127.0.0.1:8000/api/v1/consultants/me/profile', c_tok, 'Consultant storefront in Studio')
test_get('http://127.0.0.1:8000/api/v1/consultants/me/stats', c_tok, 'Consultant Stats')
test_get('http://127.0.0.1:8000/api/v1/consultants/me/availability/rules', c_tok, 'Consultant Availability Rules')
test_get('http://127.0.0.1:8000/api/v1/consultants/me/bookings', c_tok, 'Consultant Sessions & Requests queue')

test_get('http://127.0.0.1:8000/api/v1/consultants/me/profile', r_tok, 'Reader storefront in Studio')

test_get('http://127.0.0.1:8000/api/v1/consultants', a_tok, 'Admin viewing Consultant directory')
test_get('http://127.0.0.1:8000/api/v1/bookings', a_tok, 'Admin viewing Sessions')

print('ALL 12 END-TO-END VERIFICATION CHECKS PASSED!')


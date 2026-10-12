import sys, os, traceback
os.chdir('C:/Users/ASUS/Desktop/Palmistry/backend')
sys.path.insert(0, '.')
from app.services.reports.pdf_exporter import export_report_to_pdf
report = {
    "reading_title":"Test","report_type":"palmistry","title":"Palmistry Report",
    "user_name":"Alex","created_at":"2026-09-23",
    "summary":{"text":"This is a long summary with unicode: ✨🌙☀️ and some text."},
    "confidence":{"score":92,"label":"Very High"},
    "palm_features":{"element":"Fire","shape_description":"A dynamic hand.","hand_detected":"Right","landmarks_count":21},
    "lines":[{"key":"life","name":"Life Line","interpretation":"Strong"}],
    "mounts":[{"key":"venus","name":"Venus","meaning":"Love"}],
    "actionable_guidance":["Meditate daily."],
    "disclaimer":"Educational only.",
    "engine_metadata":{"engine":"E","version":"1","timestamp_utc":"2026-09-23T10:00:00Z"},
    "recommendations":{"items":["Practice mindfulness."]},
}
try:
    b = export_report_to_pdf(report)
    with open('C:/tmp/test_full.pdf','wb') as f: f.write(b)
    print('OK full len=', len(b))
except Exception as e:
    traceback.print_exc()

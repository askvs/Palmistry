import sys, os, traceback
sys.path.insert(0, '.')
os.chdir('C:/Users/ASUS/Desktop/Palmistry/backend')
from app.services.reports.pdf_exporter import export_report_to_pdf
# Complete data
report_full = {
    "reading_title":"Full","report_type":"tarot","title":"Complete Tarot",
    "user_name":"Alex","created_at":"2026-09-23","confidence":{"score":95,"label":"High"},
    "summary":"A comprehensive spiritual reading.",
    "cards":[{"name":"The Fool","position_name":"Position 1","orientation":"Upright","arcana":"Major","interpretation":"New beginnings."}],
    "spread_details":{"name":"Celtic Cross","inquiry":"Life direction"},
    "synthesis":{"elemental_dominance":"Fire","reversals_count":1},
    "narrative":{"theme":"Transformation","full_text":"Long narrative with unicode ✨🌙☀️."*10},
    "actionable_guidance":["Meditate daily.","Keep a journal."],
    "disclaimer":"Educational.",
    "engine_metadata":{"engine":"E","version":"2","timestamp_utc":"2026-09-23T10:00:00Z"},
}
b = export_report_to_pdf(report_full)
with open('test_final_full.pdf','wb') as f: f.write(b)
print('FULL OK len=',len(b))

# Missing optional
report_miss = {"reading_title":"M","report_type":"palmistry","title":"M","summary":"","engine_metadata":{"engine":"E","version":"1","timestamp_utc":""}}
b2 = export_report_to_pdf(report_miss)
with open('test_final_missing.pdf','wb') as f: f.write(b2)
print('MISSING OK len=',len(b2))

# Long + Unicode
long_text = ("Insightful analysis with unicode symbols: ✨🎆🎇☀️🌙👁️❤️🔥💫 " * 50)
report_long = {"reading_title":"L","report_type":"palmistry","title":long_text,"summary":long_text,"palm_features":{"shape_description":"Dynamic hand with ✨."},"engine_metadata":{"engine":"E","version":"1","timestamp_utc":"2026-09-23"}}
b3 = export_report_to_pdf(report_long)
with open('test_final_long.pdf','wb') as f: f.write(b3)
print('LONG OK len=',len(b3))

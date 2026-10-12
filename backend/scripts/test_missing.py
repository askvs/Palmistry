import sys,os,traceback
os.chdir("C:/Users/ASUS/Desktop/Palmistry/backend")
sys.path.insert(0,".")
from app.services.reports.pdf_exporter import export_report_to_pdf
report={"reading_title":"T","report_type":"tarot","title":"Tarot","summary":"","cards":[],"actionable_guidance":[],"disclaimer":"","engine_metadata":{"engine":"E","version":"1","timestamp_utc":""}}
try:
    b=export_report_to_pdf(report)
    with open("backend/test_missing.pdf","wb") as fh: fh.write(b)
    print("OK missing len=",len(b))
except Exception as e: traceback.print_exc()

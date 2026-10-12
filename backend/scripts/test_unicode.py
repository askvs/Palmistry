import sys,os,traceback
os.chdir("C:/Users/ASUS/Desktop/Palmistry/backend")
sys.path.insert(0,".")
from app.services.reports.pdf_exporter import export_report_to_pdf
long_text = "A" * 2000 + " ✨🎆🎇☀️🌙" * 20
report={"reading_title":"Unicode","report_type":"palmistry","title":long_text,"summary":long_text,"palm_features":{},"engine_metadata":{"engine":"E","version":"1","timestamp_utc":""}}
try:
    b=export_report_to_pdf(report)
    with open("backend/test_unicode.pdf","wb") as fh: fh.write(b)
    print("OK unicode len=",len(b))
except Exception as e: traceback.print_exc()

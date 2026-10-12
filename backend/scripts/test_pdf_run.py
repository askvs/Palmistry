import sys,os,traceback;os.chdir("C:/Users/ASUS/Desktop/Palmistry/backend");sys.path.insert(0,".");from app.services.reports.pdf_exporter import export_report_to_pdf;report={"reading_title":"T","palm_analysis":{"summary":"x"},"tarot_reading":{"summary":"y"},"personality_insights":{"summary":"z"},"life_trends":{"summary":"t"},"spiritual_guidance":{"summary":"g"},"recommendations":{"items":[]},"summary":{"text":"s"},"engine_metadata":{"engine":"E","version":"1","timestamp_utc":"2026"}};
try:b=export_report_to_pdf(report);print("OK",len(b))
except Exception as e:traceback.print_exc()

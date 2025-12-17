from app.step1_ingest import ingest_files
from app.step3_embed import build_vector_db
from app.step5_report import generate_report
from app.step6_summary import summarize_report

if __name__ == "__main__":
    ingest_files()
    build_vector_db()
    generate_report("Create a detailed analytical business report")
    summarize_report()

import os
from langchain_community.llms import Ollama
from app.config import OLLAMA_LLM, REPORT_PATH

def summarize_report():
    llm = Ollama(model=OLLAMA_LLM)

    full_report_path = os.path.join(REPORT_PATH, "full_report.md")

    with open(full_report_path, "r", encoding="utf-8") as f:
        report = f.read()

    prompt = f"""
Summarize the following report into an executive-level summary
(maximum one page, bullet points preferred):

{report}
"""

    summary = llm.invoke(prompt)

    summary_path = os.path.join(REPORT_PATH, "summary_report.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"✅ Summary report generated: {summary_path}")

if __name__ == "__main__":
    summarize_report()

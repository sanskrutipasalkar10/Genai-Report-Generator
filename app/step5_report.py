import os
from langchain_community.llms import Ollama
from app.step4_retrieve import retrieve_context
from app.config import OLLAMA_LLM, REPORT_PATH

def generate_report(query):
    os.makedirs(REPORT_PATH, exist_ok=True)

    context = retrieve_context(query)

    llm = Ollama(model=OLLAMA_LLM)

    prompt = f"""
You are a senior business analyst.

Using the following context, generate a detailed structured report with:
1. Executive Summary
2. Key Insights
3. Risks
4. Recommendations
5. Data-backed Observations

Context:
{context}
"""

    report = llm.invoke(prompt)

    output_path = os.path.join(REPORT_PATH, "full_report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"✅ Full report generated: {output_path}")

if __name__ == "__main__":
    generate_report("Generate a comprehensive analytical report")

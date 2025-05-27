import openai
import sys
import os
from dotenv import load_dotenv
import re


def extract_text_from_pdf(pdf_path):
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
    return text


def query_gpt_for_pohoda_xml(api_key, text):
    openai_client = openai.OpenAI(api_key=api_key)

    prompt = f"""
Z následujícího textu účetního dokladu vytěž data a vygeneruj XML soubor vhodný pro import do účetnictví Pohoda (typ: issuedInvoice). Uveď pouze výsledný XML bez komentáře ani formátovacích prvků Markdown:

{text}
"""

    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Jsi expert na účetní systémy a XML importy do programu Pohoda."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    # Odstranit Markdown bloky jako ```xml\n...\n```
    if content.startswith("```xml") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1])

    return content.strip()


def main():
    if len(sys.argv) != 2:
        print("Použití: python extract_pdf_to_pohoda_xml.py cesta_k_pdf")
        sys.exit(1)

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Chybí API klíč v souboru .env (proměnná OPENAI_API_KEY).")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Soubor {pdf_path} neexistuje.")
        sys.exit(1)

    print("Extrahuji text z PDF...")
    text = extract_text_from_pdf(pdf_path)

    print("Dotazuji se na ChatGPT pro XML výstup...")
    xml_result = query_gpt_for_pohoda_xml(api_key, text)

    output_path = os.path.splitext(pdf_path)[0] + ".xml"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(xml_result)

    print(f"Výsledný XML uložen do: {output_path}")


if __name__ == "__main__":
    main()

import openai
import sys
import os
import re
import xml.etree.ElementTree as ET
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import pdfplumber
from datetime import datetime
from lxml import etree


LOG_FILE = "pohoda_import.log"


def log_error(message):
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        log.write(f"{timestamp} {message}\n")


def extract_text_from_pdf(pdf_path):
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

    # Odstranění Markdown formátování
    if content.startswith("```xml") and content.endswith("```"):
        content = "\n".join(content.split("\n")[1:-1])

    return content.strip()

def validate_xml(xml_data):
    try:
        # Validace struktury
        root = etree.fromstring(xml_data.encode("utf-8"))

        # Cesta k XSD souboru (lokální, v repozitáři)
        schema_path = os.path.join("schemas", "data.xsd")

        if not os.path.exists(schema_path):
            log_error("XSD schéma nenalezeno pro validaci XML.")
            return False

        with open(schema_path, "rb") as f:
            xmlschema_doc = etree.parse(f)
            xmlschema = etree.XMLSchema(xmlschema_doc)

        if not xmlschema.validate(root):
            log_error("XSD validace selhala:")
            for error in xmlschema.error_log:
                log_error(f"  > {error}")
            return False

        return True

    except etree.XMLSyntaxError as e:
        log_error(f"XML syntax error: {str(e)}")
        return False
    except Exception as e:
        log_error(f"Neočekávaná chyba při validaci XML: {str(e)}")
        return False


def send_to_pohoda(xml_data, url, username, password, agenda, source_file):
    headers = {
        "Content-Type": "text/xml",
        "Accept": "application/xml",
        "X-AGENTA": agenda
    }

    try:
        response = requests.post(url, data=xml_data.encode("utf-8"), headers=headers, auth=HTTPBasicAuth(username, password))
        if response.status_code != 200 or "<error" in response.text.lower():
            log_error(f"Chyba importu [{source_file}]: HTTP {response.status_code} – {response.text}")
        else:
            print(f"✅ Import úspěšný: {source_file}")
    except Exception as e:
        log_error(f"Chyba HTTP při odesílání [{source_file}]: {str(e)}")


def process_pdf(pdf_path, config):
    print(f"\n📄 Zpracovávám soubor: {pdf_path}")

    try:
        text = extract_text_from_pdf(pdf_path)
        xml = query_gpt_for_pohoda_xml(config["api_key"], text)

        # FIXME:
#         if not validate_xml(xml):
#             print(f"❌ Nevalidní XML: {pdf_path}")
#             return

        xml_path = os.path.splitext(pdf_path)[0] + ".xml"
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"💾 XML uložen: {xml_path}")

        # FIXME:
        # send_to_pohoda(xml, config["pohoda_url"], config["pohoda_user"], config["pohoda_pass"], config["pohoda_agenda"], os.path.basename(pdf_path))

    except Exception as e:
        log_error(f"Výjimka při zpracování [{pdf_path}]: {str(e)}")


def main():
    if len(sys.argv) != 2:
        print("Použití: python lenka.py [soubor.pdf | složka]")
        sys.exit(1)

    load_dotenv()

    config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "pohoda_url": os.getenv("POHODA_SERVER_URL"),
        "pohoda_user": os.getenv("POHODA_USERNAME"),
        "pohoda_pass": os.getenv("POHODA_PASSWORD"),
        "pohoda_agenda": os.getenv("POHODA_AGENDA")
    }

    if not all(config.values()):
        print("Chybí jedna nebo více proměnných v .env souboru.")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path) and path.lower().endswith(".pdf"):
        process_pdf(path, config)

    elif os.path.isdir(path):
        pdf_files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print("Ve složce nebyly nalezeny žádné PDF soubory.")
            sys.exit(1)
        for pdf in pdf_files:
            process_pdf(pdf, config)

    else:
        print("Zadaná cesta není platný PDF soubor ani složka.")
        sys.exit(1)


if __name__ == "__main__":
    main()

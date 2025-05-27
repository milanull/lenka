# Extract PDF to Pohoda XML

Tento nástroj slouží k vytěžování údajů z účetních dokladů ve formátu PDF a převodu těchto údajů do XML struktury vhodné pro import do účetního systému Pohoda.

## Požadavky

* Python 3.8 nebo vyšší
* OpenAI účet a API klíč

## Instalace

1. Naklonujte repozitář nebo stáhněte soubory:

   ```bash
   git clone https://example.com/lenka.git
   cd lenka
   ```

2. Vytvořte a aktivujte virtuální prostředí (doporučeno):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Na Windows: .venv\Scripts\activate
   ```

3. Nainstalujte závislosti:

   ```bash
   pip install -r requirements.txt
   ```

4. Vytvořte soubor `.env` s obsahem:

   ```env
   OPENAI_API_KEY=sk-tvuj_klic_zde
   ```

## Použití

Spusťte skript s cestou k PDF souboru jako argumentem:

```bash
python lenka.py ./cesta/k/dokladu.pdf
```

Program:

* Načte a vytěží text z PDF
* Pomocí GPT-4 vygeneruje XML pro účetnictví Pohoda
* Výstup uloží do souboru se stejným názvem jako PDF, ale s příponou `.xml`

## Poznámky

* Použitý model je `gpt-4`, což může vyžadovat odpovídající oprávnění vašeho OpenAI účtu.
* XML výstup je automaticky očištěn od Markdown formátování.

## Licence

MIT License

---

V případě potřeby rozšíření (vícenásobné soubory, validace XML, přímý import do Pohody) kontaktujte autora nebo otevřete issue.

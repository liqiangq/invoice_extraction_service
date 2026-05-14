# Data Folder

Use this folder for local sample documents while developing extraction prompts and tests.

Recommended layout:

```text
data/
  invoices/
    en/
    es/
    zh/
    fr/
    mandarin/
  job_descriptions/
    en/
    es/
    zh/
    fr/
```

Put files under the language code that matches the document text. For example:

```text
data/invoices/es/factura-001.pdf
data/invoices/zh/invoice-002.txt
data/invoices/fr/facture-003.png
data/invoices/mandarin/mandarin-synth_0049.png
```

Keep real invoices out of git. If you need committed test examples, anonymize them first and place them under `tests/fixtures/`.

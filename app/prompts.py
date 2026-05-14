INVOICE_EXTRACTION_PROMPT = """Extract invoice data from the document text.

Return one valid JSON object only. Do not include markdown, comments, or extra text.
Use this exact schema:
{
  "supplier_name": "string or null",
  "invoice_number": "string or null",
  "invoice_date": "string or null",
  "due_date": "string or null",
  "currency": "string or null",
  "subtotal": "number or null",
  "gst": "number or null",
  "total": "number or null",
  "confidence": "number from 0 to 1",
  "missing_fields": ["field names that could not be confidently extracted"]
}
"""

JOB_DESCRIPTION_EXTRACTION_PROMPT = """Extract job description data from the document text.

Return one valid JSON object only. Do not include markdown, comments, or extra text.
Use this exact schema:
{
  "title": "string or null",
  "company": "string or null",
  "required_skills": ["strings"],
  "responsibilities": ["strings"],
  "salary_range": "string or null"
}
"""

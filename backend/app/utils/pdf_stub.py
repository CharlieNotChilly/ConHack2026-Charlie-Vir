import base64


def placeholder_pdf_base64() -> str:
    # Minimal valid PDF with a single empty page.
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"0000000010 00000 n \n0000000060 00000 n \n0000000114 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n168\n%%EOF"
    )
    return base64.b64encode(pdf_bytes).decode("ascii")

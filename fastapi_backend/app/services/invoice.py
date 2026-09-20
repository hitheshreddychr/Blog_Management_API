import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


INVOICE_DIR = "media/invoices"

os.makedirs(INVOICE_DIR, exist_ok=True)


def get_invoice_font():
    font_paths = [
        r"C:\Windows\Fonts\Nirmala.ttf",
        r"C:\Windows\Fonts\NirmalaUI.ttf",
        r"C:\Windows\Fonts\arialuni.ttf",
        r"C:\Windows\Fonts\DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(
                    TTFont(
                        "InvoiceUnicode",
                        font_path,
                    )
                )
                return "InvoiceUnicode"
            except Exception:
                continue

    return "Helvetica"


def generate_invoice(
    billing_id: int,
    username: str,
    plan_name: str,
    price,
    start_date: datetime,
    end_date: datetime,
    transaction_id: str,
) -> str:
    filename = f"invoice_{billing_id}.pdf"

    file_path = os.path.join(
        INVOICE_DIR,
        filename,
    )

    font_name = get_invoice_font()

    pdf = canvas.Canvas(
        file_path,
        pagesize=A4,
    )

    width, height = A4

    pdf.setTitle(
        f"Invoice {billing_id}"
    )

    pdf.setFont(
        font_name,
        20,
    )

    pdf.drawString(
        50,
        height - 60,
        "BLOG MANAGEMENT API",
    )

    pdf.setFont(
        font_name,
        16,
    )

    pdf.drawString(
        50,
        height - 100,
        "SUBSCRIPTION INVOICE",
    )

    pdf.setFont(
        font_name,
        11,
    )

    y_position = height - 150

    currency_symbol = "₹"

    if font_name == "Helvetica":
        currency_symbol = "INR "

    invoice_details = [
        ("Invoice ID", str(billing_id)),
        ("User Name", username),
        ("Plan Name", plan_name),
        ("Price", f"{currency_symbol}{price}"),
        (
            "Start Date",
            start_date.strftime("%Y-%m-%d %H:%M:%S"),
        ),
        (
            "End Date",
            end_date.strftime("%Y-%m-%d %H:%M:%S"),
        ),
        ("Transaction ID", transaction_id),
    ]

    for label, value in invoice_details:
        pdf.setFont(
            font_name,
            11,
        )

        pdf.drawString(
            60,
            y_position,
            f"{label}:",
        )

        pdf.setFont(
            font_name,
            11,
        )

        pdf.drawString(
            180,
            y_position,
            str(value),
        )

        y_position -= 30

    pdf.setFont(
        font_name,
        12,
    )

    pdf.drawString(
        60,
        y_position - 20,
        "Thank you for subscribing!",
    )

    pdf.save()

    return f"/media/invoices/{filename}"
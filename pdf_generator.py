import os
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from database import db


def link_callback(uri, rel):
    base_dir = os.path.dirname(__file__)

    if uri.startswith("/signatures/"):
        return os.path.join(base_dir, "signatures", uri.replace("/signatures/", ""))

    if uri.startswith("/"):
        return os.path.join(base_dir, "public", uri.lstrip("/"))

    return uri


def generate_invoice_pdf(invoice_data):
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))

    template_name = "invoice_template_visual.html" if invoice_data.get("template") == "visual" else "invoice_template.html"
    template = env.get_template(template_name)

    settings = db.get_settings()

    COMPANY_NAME = settings.get('company_name', "Medicine Wheel Ranch Inc.")
    COMPANY_ADDRESS = settings.get('company_address', "443 North Russell Road, Russell, ON, Canada - K4R 1E5")
    COMPANY_PHONE = settings.get('company_phone', "(613) 266-4806")

    logo_path = settings.get('default_logo_path')
    LOGO_IMAGE = None

    if logo_path:
        if not os.path.isfile(logo_path):
            folder = os.path.dirname(logo_path)
            filename_lower = os.path.basename(logo_path).lower()

            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.lower() == filename_lower:
                        logo_path = os.path.join(folder, f)
                        break

        if os.path.isfile(logo_path):
            LOGO_IMAGE = f"/{os.path.basename(logo_path)}"

    DEFAULT_SHIPPING_METHOD = settings.get('default_shipping_method', "Seller")
    DEFAULT_SHIPPING_TERMS = settings.get('default_shipping_terms', "Seller")

    items = invoice_data.get('items', [])
    for item in items:
        item['total'] = item['quantity'] * item['unit_price']

    subtotal = sum(item['total'] for item in items)
    tax = subtotal * (float(invoice_data.get('tax_rate', 13)) / 100)
    shipping = float(invoice_data.get('shipping_cost', 0))
    total = subtotal + tax + shipping

    signature = invoice_data.get('signature', {})

    template_data = {
        'LOGO_IMAGE': LOGO_IMAGE,
        'COMPANY_NAME': COMPANY_NAME,
        'COMPANY_ADDRESS': COMPANY_ADDRESS,
        'COMPANY_PHONE': COMPANY_PHONE,

        'INVOICE_NUMBER': invoice_data['invoice_number'],
        'DATE': invoice_data['date'],

        'customer_name': invoice_data.get('customer_name', ''),
        'customer_address': invoice_data.get('customer_address', ''),
        'customer_city': invoice_data.get('customer_city', ''),
        'customer_phone': invoice_data.get('customer_phone', ''),
        'customer_email': invoice_data.get('customer_email', ''),

        'vendor_name': invoice_data.get('vendor_name', ''),
        'vendor_address': invoice_data.get('vendor_address', ''),
        'vendor_city': invoice_data.get('vendor_city', ''),
        'vendor_phone': invoice_data.get('vendor_phone', ''),
        'vendor_email': invoice_data.get('vendor_email', ''),

        'shipping_method': invoice_data.get('shipping_method', DEFAULT_SHIPPING_METHOD),
        'shipping_terms': invoice_data.get('shipping_terms', DEFAULT_SHIPPING_TERMS),
        'delivery_date': invoice_data.get('delivery_date', 'TBD'),

        'HST_GST_NUMBER': invoice_data.get('hst_gst_number', ''),
        'ITEMS': items,
        'SUBTOTAL': f"{subtotal:.2f}",
        'TAX_RATE': f"{invoice_data.get('tax_rate', 13)}%",
        'TAX': f"{tax:.2f}",
        'SHIPPING': f"{shipping:.2f}",
        'GRAND_TOTAL': f"{total:.2f}",

        'COMMENTS': invoice_data.get('comments', ''),
        'TERMS_CONDITIONS': invoice_data.get('terms_conditions', ''),

        'SIGNATURE_NAME': signature.get('name', ''),
        'SIGNATURE_POSITION': signature.get('position', ''),
        'SIGNATURE_IMAGE': f"/signatures/{signature.get('image')}" if signature.get('image') else None,

        'CREATED_BY': invoice_data.get('created_by', 'User')
    }

    html_content = template.render(**template_data)

    vendor_clean = (invoice_data.get('vendor_name', 'Unknown')).replace(' ', '_')
    vendor_clean = ''.join(c for c in vendor_clean if c.isalnum() or c in '_-')
    date = invoice_data['date']
    number = invoice_data['invoice_number'].split('-')[1]
    type_clean = invoice_data['type']

    filename = f"{date} - MWR-{number} - {type_clean} PO - {vendor_clean}.pdf"
    pdf_path = os.path.join(os.path.dirname(__file__), 'pdfs', filename)

    with open(pdf_path, "wb") as pdf_file:
        pisa_status = pisa.CreatePDF(
            html_content,
            dest=pdf_file,
            link_callback=link_callback
        )

    if pisa_status.err:
        raise Exception(f"PDF generation failed: {pisa_status.err}")

    return pdf_path

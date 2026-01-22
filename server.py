from flask import Flask, request, jsonify, session, send_file, send_from_directory, render_template
from flask_session import Session
import os
import sys
import webbrowser
import threading
import time
from werkzeug.utils import secure_filename
from database import db
from pdf_generator import generate_invoice_pdf
from excel_export import export_invoices_to_excel

app = Flask(__name__, static_folder='public', static_url_path='')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['SECRET_KEY'] = 'portable-invoice-software'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(BASE_DIR, 'data', 'sessions')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'signatures')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'pdfs'), exist_ok=True)

Session(app)


@app.route('/')
def index():
    return send_file('public/index.html')


@app.route('/api/settings/hst-gst')
def get_hst_gst_settings():
    return jsonify({
        'default_hst_gst': db.get_default_hst_gst(),
        'current': db.get_default_hst_gst()
    })


@app.route('/api/settings/hst-gst', methods=['POST'])
def set_hst_gst():
    data = request.json
    db.set_default_hst_gst(data['hst_gst_number'])
    return jsonify({'success': True})


@app.route('/api/hst-gst', methods=['POST'])
def add_hst_gst_number():
    data = request.json or {}
    number = data.get('number')
    if number is None:
        number = data.get('hst_gst_number')
    if number is None:
        return jsonify({'error': 'No HST/GST number provided'}), 400
    db.set_default_hst_gst(number)
    return jsonify({'success': True, 'hst_gst_number': number})


@app.route('/api/signatures', methods=['GET'])
def get_signatures():
    signatures = db.get_all_signatures()
    for sig in signatures:
        sig['image_path'] = os.path.basename(sig['image_path'])
    return jsonify(signatures)


@app.route('/api/signatures/default')
def get_default_signature():
    sig = db.get_default_signature()
    if sig:
        sig['image_path'] = os.path.basename(sig['image_path'])
        return jsonify(sig)
    return jsonify(None)


@app.route('/api/signatures', methods=['POST'])
def upload_signature_legacy():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        name = request.form.get('name', 'Unknown')
        position = request.form.get('position', '')
        signature_id = db.add_signature(name, position, filepath)
        return jsonify({'id': signature_id, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signatures/upload', methods=['POST'])
def upload_signature():
    try:
        if 'signature' not in request.files:
            return jsonify({'error': 'No signature file provided'}), 400
        file = request.files['signature']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        name = request.form.get('name', 'Unknown')
        position = request.form.get('position', '')
        signature_id = db.add_signature(name, position, filepath)
        return jsonify({
            'success': True,
            'id': signature_id,
            'image_path': filename,
            'name': name,
            'position': position
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signatures/<int:sig_id>/set-default', methods=['POST'])
def set_default_signature(sig_id):
    db.set_default_signature(sig_id)
    return jsonify({'success': True})


@app.route('/signatures/<filename>')
def serve_signature(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/signatures/<int:sig_id>/edit', methods=['POST'])
def edit_signature(sig_id):
    data = request.json
    db.update_signature(sig_id, data['name'], data['position'])
    return jsonify({'success': True})


@app.route('/api/signatures/<int:sig_id>/delete', methods=['DELETE'])
def delete_signature(sig_id):
    db.delete_signature(sig_id)
    return jsonify({'success': True})


@app.route('/api/settings/company', methods=['GET'])
def get_company_settings():
    try:
        settings = db.get_settings()
        logo_path = settings.get('default_logo_path')
        if logo_path:
            filename = os.path.basename(logo_path)
            settings['default_logo_url'] = f"/{filename}"
        else:
            settings['default_logo_url'] = None
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/company', methods=['POST'])
def update_company_settings():
    try:
        data = request.json or {}
        current = db.get_settings()
        existing_logo_path = current.get('default_logo_path')
        incoming_logo = data.get('default_logo_path')
        if incoming_logo and not incoming_logo.startswith('/'):
            logo_path = incoming_logo
        else:
            logo_path = existing_logo_path
        db.update_settings({
            'company_name': data.get('company_name'),
            'company_address': data.get('company_address'),
            'company_phone': data.get('company_phone'),
            'default_logo_path': logo_path,
            'default_shipping_method': data.get('default_shipping_method'),
            'default_shipping_terms': data.get('default_shipping_terms')
        })
        return jsonify({'success': True, 'message': 'Company settings updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/settings/logo', methods=['POST'])
def upload_company_logo():
    try:
        if 'logo' not in request.files:
            return jsonify({'error': 'No logo file provided'}), 400
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not file.content_type.startswith('image/'):
            return jsonify({'error': 'File must be an image'}), 400
        filename = secure_filename(file.filename)
        save_path = os.path.join(BASE_DIR, 'public', filename)
        file.save(save_path)
        db.update_settings({'default_logo_path': save_path})
        return jsonify({
            'success': True,
            'logo_file': filename,
            'logo_url': f"/{filename}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/next-invoice-number')
def get_next_invoice_number():
    try:
        number = db.get_next_invoice_number()
        return jsonify({'invoice_number': number})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    try:
        vendors = db.get_all_vendors()
        return jsonify(vendors)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vendors', methods=['POST'])
def add_vendor():
    try:
        data = request.json
        vendor_id = db.add_vendor(data['name'], data['address'], data['contact'])
        return jsonify({'id': vendor_id, 'message': 'Vendor saved'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vendors/<int:vendor_id>', methods=['PUT'])
def update_vendor(vendor_id):
    try:
        data = request.json
        db.update_vendor(vendor_id, data['name'], data['address'], data['contact'])
        return jsonify({'success': True, 'message': 'Vendor updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/vendors/<int:vendor_id>', methods=['DELETE'])
def delete_vendor(vendor_id):
    try:
        db.delete_vendor(vendor_id)
        return jsonify({'success': True, 'message': 'Vendor deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    try:
        invoices = db.get_all_invoices()
        return jsonify(invoices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/invoices', methods=['POST'])
def create_invoice():
    try:
        invoice_data = request.json
        invoice_data['created_by'] = session.get('username', 'User')

        signature = invoice_data.get('signature')
        if signature:
            invoice_data['signature_id'] = signature.get('id')

        pdf_path = generate_invoice_pdf(invoice_data)

        invoice_id = db.save_invoice(invoice_data)
        db.update_invoice_pdf_path(invoice_id, pdf_path)

        return jsonify({
            'success': True,
            'invoice_id': invoice_id,
            'pdf_path': pdf_path,
            'message': 'Invoice created successfully!'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================
# Invoice Live Preview
# ============================

@app.route('/preview-invoice/<int:invoice_id>')
def preview_invoice(invoice_id):
    try:
        invoice = db.get_invoice(invoice_id)
        if not invoice:
            return "Invoice not found", 404

        template_override = request.args.get("template")
        if template_override:
            invoice["template"] = template_override

        settings = db.get_settings()

        signature = None
        if invoice.get('signature_id'):
            signature = db.get_signature(invoice['signature_id'])
            if signature:
                signature['image_path'] = f"/signatures/{os.path.basename(signature['image_path'])}"

        logo_image = None
        if settings.get('default_logo_path'):
            logo_image = f"/{os.path.basename(settings.get('default_logo_path'))}"

        template_name = "invoice_template_visual.html" if invoice.get("template") == "visual" else "invoice_template.html"

        template_data = {
            'COMPANY_NAME': settings.get('company_name'),
            'COMPANY_ADDRESS': settings.get('company_address'),
            'COMPANY_PHONE': settings.get('company_phone'),
            'LOGO_IMAGE': logo_image,

            'INVOICE_NUMBER': invoice.get('invoice_number'),
            'DATE': invoice.get('date'),

            'customer_name': invoice.get('customer_name'),
            'customer_address': invoice.get('customer_address'),
            'customer_city': invoice.get('customer_city'),
            'customer_phone': invoice.get('customer_phone'),
            'customer_email': invoice.get('customer_email'),

            'vendor_name': invoice.get('vendor_name'),
            'vendor_address': invoice.get('vendor_address'),
            'vendor_city': invoice.get('vendor_city'),
            'vendor_phone': invoice.get('vendor_phone'),
            'vendor_email': invoice.get('vendor_email'),

            'shipping_method': invoice.get('shipping_method'),
            'shipping_terms': invoice.get('shipping_terms'),
            'delivery_date': invoice.get('delivery_date'),

            'ITEMS': invoice.get('items', []),

            'HST_GST_NUMBER': invoice.get('hst_gst_number'),
            'TAX_RATE': f"{invoice.get('tax_rate', 13)}%",
            'TAX': f"{invoice.get('tax', 0):.2f}",
            'SHIPPING': f"{invoice.get('shipping_cost', 0):.2f}",
            'GRAND_TOTAL': f"{invoice.get('grand_total', 0):.2f}",

            'COMMENTS': invoice.get('comments'),
            'TERMS_CONDITIONS': invoice.get('terms_conditions'),

            'SIGNATURE_NAME': signature.get('name') if signature else "",
            'SIGNATURE_POSITION': signature.get('position') if signature else "",
            'SIGNATURE_IMAGE': signature.get('image_path') if signature else None,

            'PDF_FILENAME': os.path.basename(invoice.get('pdf_path', "")) if invoice.get('pdf_path') else ""
        }

        return render_template(template_name, **template_data)
    except Exception as e:
        return f"Error: {str(e)}", 500


@app.route('/api/export-excel')
def export_excel():
    try:
        invoices = db.get_all_invoices()
        excel_path = export_invoices_to_excel(invoices)
        return send_file(excel_path, as_attachment=True, download_name='invoice_registry.xlsx')
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/pdfs/<filename>')
def serve_pdf(filename):
    return send_from_directory('pdfs', filename)


def open_browser():
    time.sleep(2)
    webbrowser.open('http://localhost:3000')
    print("🌐 Browser opened automatically!")


if __name__ == '__main__':
    db.init()

    print("="*60)
    print("✅ PORTABLE Invoice Software")
    print("="*60)
    print(f"📁 Location: {BASE_DIR}")
    print(f"💾 Database: {db.db_path}")
    print(f"📄 PDFs: {os.path.join(BASE_DIR, 'pdfs')}")
    print(f"✍️  Signatures: {app.config['UPLOAD_FOLDER']}")
    print(f"🌐 Server: http://localhost:3000")
    print("="*60)
    print("Ready to use by Rasesh Pradhan")
    print("="*60)

    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=3000, debug=False, threaded=True)

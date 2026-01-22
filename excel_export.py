import os
import tempfile
from openpyxl import Workbook
from openpyxl.styles import Font


def export_invoices_to_excel(invoices):
    """
    Export invoice records to an Excel file.
    Returns the full path to the generated .xlsx file.
    """

    wb = Workbook()
    ws = wb.active
    ws.title = "Invoices"

    # ------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------
    headers = [
        'Invoice Number',
        'Date',
        'Type',
        'Vendor',
        'Status',
        'Created By',
        'PDF Path'
    ]

    ws.append(headers)

    # Make header bold
    for cell in ws[1]:
        cell.font = Font(bold=True)

    # Freeze header row
    ws.freeze_panes = "A2"

    # ------------------------------------------------------------
    # Data rows
    # ------------------------------------------------------------
    for inv in invoices:
        ws.append([
            inv.get('invoice_number', '') or '',
            inv.get('date', '') or '',
            inv.get('type', '') or '',
            inv.get('vendor_name', 'N/A') or 'N/A',
            inv.get('status', '') or '',
            inv.get('created_by', '') or '',
            inv.get('pdf_path', '') or ''
        ])

    # ------------------------------------------------------------
    # Auto-size columns (max width 50)
    # ------------------------------------------------------------
    for col in ws.columns:
        max_length = 0
        column_letter = col[0].column_letter

        for cell in col:
            try:
                value = str(cell.value)
                if len(value) > max_length:
                    max_length = len(value)
            except Exception:
                pass

        ws.column_dimensions[column_letter].width = min(max_length + 2, 50)

    # ------------------------------------------------------------
    # Save to temp file
    # ------------------------------------------------------------
    safe_pid = str(os.getpid())
    temp_filename = f"invoice_registry_{safe_pid}.xlsx"
    temp_path = os.path.join(tempfile.gettempdir(), temp_filename)

    wb.save(temp_path)
    return temp_path

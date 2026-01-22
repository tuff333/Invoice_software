// Dashboard functions
async function loadInvoices() {
    try {
        console.log("Loading invoices...");
        const response = await fetch('/api/invoices');
        const invoices = await response.json();
        
        console.log("Invoices loaded:", invoices.length);
        document.getElementById('totalCount').textContent = invoices.length;
        
        const currentMonth = new Date().getMonth();
        const monthCount = invoices.filter(inv => new Date(inv.date.replace(/-/g, '/')).getMonth() === currentMonth).length;
        document.getElementById('monthCount').textContent = monthCount;
        
        const tbody = document.getElementById('invoiceTable');
        tbody.innerHTML = invoices.map(inv => {
            const pdfFile = inv.pdf_path
                ? inv.pdf_path.replace(/\\/g, '/').split('/').pop()
                : null;

            return `
                <tr>
                    <td>${inv.invoice_number}</td>
                    <td>${inv.date}</td>
                    <td><span class="badge">${inv.type}</span></td>
                    <td>${inv.vendor_name || 'N/A'}</td>
                    <td><span class="badge badge-${inv.status.toLowerCase()}">${inv.status}</span></td>
                    <td>
                        ${pdfFile ? `<a href="/pdfs/${pdfFile}" target="_blank" class="btn-small">📄 PDF</a>` : ''}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Failed to load invoices:', err);
    }
}

function exportToExcel() {
    console.log("Exporting to Excel...");
    window.location.href = '/api/export-excel';
}

// Search functionality
if (document.getElementById('search')) {
    document.getElementById('search').addEventListener('input', (e) => {
        const filter = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#invoiceTable tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(filter) ? '' : 'none';
        });
    });
}

// Load invoices on page load
if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
    document.addEventListener('DOMContentLoaded', loadInvoices);
}

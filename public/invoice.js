let signatures = [];
let currentInvoiceId = null;

document.addEventListener('DOMContentLoaded', async () => {
    try {
        document.getElementById('date').valueAsDate = new Date();

        const response = await fetch('/api/next-invoice-number');
        const data = await response.json();
        document.getElementById('invoice_number').value = data.invoice_number;

        await loadVendors();
        await loadSignatures();
        await loadDefaultSignature();

        addItemRow();
        calculateTotals();

        document.getElementById('itemsBody').addEventListener('input', calculateTotals);
        document.getElementById('tax_rate').addEventListener('input', calculateTotals);
        document.getElementById('shipping_cost').addEventListener('input', calculateTotals);

        document.getElementById('signatureSelect').addEventListener('change', updateSignaturePreview);

        document.getElementById("previewInvoiceBtn").addEventListener("click", function () {
            if (!currentInvoiceId) {
                alert("Please create the invoice first (submit the form).");
                return;
            }
            const template = document.getElementById("templateSelect").value;
            window.open(`/preview-invoice/${currentInvoiceId}?template=${template}`, "_blank");
        });

    } catch (err) {
        console.error("Error loading page:", err);
    }
});

// ===============================
// LOAD VENDORS
// ===============================
async function loadVendors() {
    const response = await fetch('/api/vendors');
    const vendors = await response.json();
    const select = document.getElementById('vendorSelect');
    select.innerHTML = '<option value="">-- Select Vendor --</option>';
    vendors.forEach(v => {
        select.innerHTML += `<option value="${v.id}" data-address="${v.address}" data-contact="${v.contact}">${v.name}</option>`;
    });
}

// ===============================
// LOAD SIGNATURES
// ===============================
async function loadSignatures() {
    const response = await fetch('/api/signatures');
    signatures = await response.json();
    const select = document.getElementById('signatureSelect');
    select.innerHTML = '<option value="">-- No Signature --</option>';
    signatures.forEach(sig => {
        select.innerHTML += `<option value="${sig.id}" data-image="${sig.image_path}" data-name="${sig.name}" data-position="${sig.position}">${sig.name} (${sig.position})</option>`;
    });
}

async function loadDefaultSignature() {
    const response = await fetch('/api/signatures/default');
    const sig = await response.json();
    if (sig && sig.id) {
        document.getElementById('signatureSelect').value = sig.id;
        showSignaturePreview(sig);
    }
}

// ===============================
// SIGNATURE PREVIEW
// ===============================
function updateSignaturePreview() {
    const sel = document.getElementById('signatureSelect');
    const opt = sel.selectedOptions[0];
    if (!opt || !opt.value) {
        document.getElementById('signaturePreview').style.display = 'none';
        return;
    }
    showSignaturePreview({
        name: opt.dataset.name,
        position: opt.dataset.position,
        image_path: opt.dataset.image
    });
}

function showSignaturePreview(sig) {
    const preview = document.getElementById('signaturePreview');
    const img = document.getElementById('signatureImage');
    const info = document.getElementById('signatureInfo');

    const imagePath = sig.image_path || sig.image;

    if (imagePath) {
        img.src = `/signatures/${imagePath}`;
        img.style.display = 'inline-block';
        info.innerHTML = `<strong>${sig.name}</strong><br>${sig.position || ''}`;
        preview.style.display = 'block';
    } else {
        preview.style.display = 'none';
    }
}

// ===============================
// ADD ITEM ROW
// ===============================
function addItemRow() {
    const tbody = document.getElementById('itemsBody');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td><input type="text" class="lot-number" style="width:80px;"></td>
        <td><input type="text" class="item-desc" style="width:100%;" required></td>
        <td><input type="number" class="qty" style="width:60px;" step="0.01"></td>
        <td>
            <select class="units" style="width:80px;">
                <option value="Gram">Gram</option>
                <option value="Kilogram">Kilogram</option>
            </select>
        </td>
        <td><input type="number" class="unit-price" style="width:80px;" step="0.01"></td>
        <td class="item-total" style="text-align:right; font-weight:bold;">$0.00</td>
        <td><button type="button" onclick="this.closest('tr').remove(); calculateTotals();">Remove</button></td>
    `;
    tbody.appendChild(row);
}

// ===============================
// CALCULATE TOTALS
// ===============================
function calculateTotals() {
    const rows = document.querySelectorAll('#itemsBody tr');
    let subtotal = 0;

    rows.forEach(row => {
        const qty = parseFloat(row.querySelector('.qty').value) || 0;
        const price = parseFloat(row.querySelector('.unit-price').value) || 0;
        const total = qty * price;
        row.querySelector('.item-total').textContent = `$${total.toFixed(2)}`;
        subtotal += total;
    });

    const taxRate = parseFloat(document.getElementById('tax_rate').value) || 13;
    const shipping = parseFloat(document.getElementById('shipping_cost').value) || 0;
    const tax = subtotal * (taxRate / 100);
    const grandTotal = subtotal + tax + shipping;

    document.getElementById('grand_total').value = `$${grandTotal.toFixed(2)}`;
}

// ===============================
// SUBMIT INVOICE
// ===============================
document.getElementById('invoiceForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const items = Array.from(document.querySelectorAll('#itemsBody tr')).map(row => ({
        lot_number: row.querySelector('.lot-number').value,
        item: row.querySelector('.item-desc').value,
        quantity: parseFloat(row.querySelector('.qty').value) || 0,
        units: row.querySelector('.units').value,
        unit_price: parseFloat(row.querySelector('.unit-price').value) || 0
    })).filter(item => item.item);

    if (items.length === 0) {
        alert('Add at least one item');
        return;
    }

    const sigSelect = document.getElementById('signatureSelect');
    const sigOption = sigSelect.selectedOptions[0];

    const template = document.getElementById('templateSelect').value;

    const invoiceData = {
        invoice_number: document.getElementById('invoice_number').value,
        date: document.getElementById('date').value,
        type: document.getElementById('type').value,
        vendor_id: document.getElementById('vendorSelect').value,
        vendor_name: document.getElementById('vendorSelect').selectedOptions[0]?.text || '',
        vendor_address: document.getElementById('vendorSelect').selectedOptions[0]?.dataset.address || '',
        vendor_contact: document.getElementById('vendorSelect').selectedOptions[0]?.dataset.contact || '',
        hst_gst_number: document.getElementById('hstGstSelect').value,
        shipping_method: document.getElementById('shipping_method').value || '',
        shipping_terms: document.getElementById('shipping_terms').value || '',
        delivery_date: document.getElementById('delivery_date').value || '',
        comments: document.getElementById('comments').value,
        terms_conditions: document.getElementById('terms_conditions').value,
        signature: sigOption && sigOption.value ? {
            id: sigOption.value,
            name: sigOption.dataset.name,
            position: sigOption.dataset.position,
            image: sigOption.dataset.image
        } : null,
        tax_rate: parseFloat(document.getElementById('tax_rate').value) || 13,
        shipping_cost: parseFloat(document.getElementById('shipping_cost').value) || 0,
        notes: '',
        items: items,
        template: template
    };

    try {
        const response = await fetch('/api/invoices', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(invoiceData)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            currentInvoiceId = result.invoice_id;

            const pdfFile = result.pdf_path.replace(/\\/g, '/').split('/').pop();
            window.open('/pdfs/' + pdfFile, '_blank');

            alert('Invoice created. You can now use Preview to see the HTML version.');
        } else {
            alert('Error: ' + (result.error || 'Unknown error'));
        }

    } catch (err) {
        alert('Network error: ' + err.message);
    }
});

// ===============================
// ADD NEW VENDOR
// ===============================
function showAddVendor() {
    const name = prompt("Enter vendor name:");
    if (!name) return;

    const address = prompt("Enter vendor address:") || "";
    const contact = prompt("Enter vendor contact:") || "";

    fetch('/api/vendors', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, address, contact })
    })
    .then(res => res.json())
    .then(data => {
        alert("Vendor added successfully");
        loadVendors();
    })
    .catch(err => alert("Error adding vendor"));
}

// ===============================
// ADD NEW HST/GST NUMBER
// ===============================
function addHstGstNumber() {
    const number = prompt("Enter new HST/GST number:");
    if (!number) return;

    fetch('/api/hst-gst', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ number })
    })
    .then(res => res.json())
    .then(data => {
        alert("HST/GST number added");

        const select = document.getElementById('hstGstSelect');
        select.innerHTML += `<option value="${number}">${number}</option>`;
        select.value = number;
    })
    .catch(err => alert("Error adding HST/GST number"));
}

// ===============================
// UPLOAD SIGNATURE
// ===============================
function uploadSignature() {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";

    fileInput.onchange = async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const name = prompt("Enter signature name:") || "Unknown";
        const position = prompt("Enter position:") || "";

        const formData = new FormData();
        formData.append("signature", file);
        formData.append("name", name);
        formData.append("position", position);

        try {
            const res = await fetch("/api/signatures/upload", {
                method: "POST",
                body: formData
            });

            const result = await res.json();

            if (result.success) {
                alert("Signature uploaded successfully");
                loadSignatures();
            } else {
                alert(result.error || "Upload failed");
            }
        } catch (err) {
            alert("Error uploading signature: " + err.message);
        }
    };

    fileInput.click();
}

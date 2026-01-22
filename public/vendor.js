// ============================
// Vendor Management (v02)
// ============================

document.addEventListener("DOMContentLoaded", () => {
    loadVendors();
});

// Cached vendor list
let vendors = [];

// ============================
// Load Vendors
// ============================
async function loadVendors() {
    try {
        const res = await fetch("/api/vendors");
        vendors = await res.json();

        populateVendorDropdown();
        populateVendorTable(); // if vendor table exists
    } catch (err) {
        console.error("Failed to load vendors:", err);
    }
}

// ============================
// Populate Vendor Dropdown (invoice.html)
// ============================
function populateVendorDropdown() {
    const vendorSelect = document.getElementById("vendorSelect");
    if (!vendorSelect) return;

    vendorSelect.innerHTML = `<option value="">Select Vendor</option>`;

    vendors.forEach(v => {
        const opt = document.createElement("option");
        opt.value = v.id;
        opt.textContent = v.name;
        vendorSelect.appendChild(opt);
    });
}

// ============================
// Populate Vendor Table (settings/vendors.html)
// ============================
function populateVendorTable() {
    const table = document.getElementById("vendorTable");
    if (!table) return;

    table.innerHTML = "";

    vendors.forEach(v => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${v.name}</td>
            <td>${v.address}</td>
            <td>${v.contact}</td>
            <td>
                <button class="btn-small" onclick="openEditVendor(${v.id})">Edit</button>
                <button class="btn-danger-small" onclick="deleteVendor(${v.id})">Delete</button>
            </td>
        `;

        table.appendChild(row);
    });
}

// ============================
// Add Vendor
// ============================
async function addVendor() {
    const name = document.getElementById("vendorName").value;
    const address = document.getElementById("vendorAddress").value;
    const contact = document.getElementById("vendorContact").value;

    if (!name.trim()) {
        alert("Vendor name is required");
        return;
    }

    try {
        const res = await fetch("/api/vendors", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, address, contact })
        });

        const result = await res.json();

        if (result.id) {
            alert("Vendor added");
            loadVendors();
        }
    } catch (err) {
        alert("Error adding vendor");
    }
}

// ============================
// Edit Vendor (open modal)
// ============================
function openEditVendor(id) {
    const vendor = vendors.find(v => v.id === id);
    if (!vendor) return;

    document.getElementById("editVendorId").value = vendor.id;
    document.getElementById("editVendorName").value = vendor.name;
    document.getElementById("editVendorAddress").value = vendor.address;
    document.getElementById("editVendorContact").value = vendor.contact;

    document.getElementById("editVendorModal").style.display = "block";
}

// ============================
// Save Edited Vendor
// ============================
async function saveVendorChanges() {
    const id = document.getElementById("editVendorId").value;
    const name = document.getElementById("editVendorName").value;
    const address = document.getElementById("editVendorAddress").value;
    const contact = document.getElementById("editVendorContact").value;

    try {
        const res = await fetch(`/api/vendors/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, address, contact })
        });

        const result = await res.json();

        if (result.success) {
            alert("Vendor updated");
            document.getElementById("editVendorModal").style.display = "none";
            loadVendors();
        }
    } catch (err) {
        alert("Error updating vendor");
    }
}

// ============================
// Delete Vendor
// ============================
async function deleteVendor(id) {
    if (!confirm("Delete this vendor?")) return;

    try {
        const res = await fetch(`/api/vendors/${id}`, { method: "DELETE" });
        const result = await res.json();

        if (result.success) {
            alert("Vendor deleted");
            loadVendors();
        }
    } catch (err) {
        alert("Error deleting vendor");
    }
}

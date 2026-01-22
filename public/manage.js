// ===============================
// LOAD EVERYTHING ON PAGE LOAD
// ===============================
document.addEventListener("DOMContentLoaded", () => {
    loadVendors();
    loadHstNumbers();
    loadSignatures();
});


// ===============================
// VENDORS
// ===============================
async function loadVendors() {
    const res = await fetch("/api/vendors");
    const vendors = await res.json();

    const table = document.getElementById("vendorTable");
    table.innerHTML = "";

    vendors.forEach(v => {
        table.innerHTML += `
            <tr>
                <td>${v.name}</td>
                <td>${v.address}</td>
                <td>${v.contact}</td>
                <td>
                    <button class="btn-small" onclick="editVendor(${v.id}, '${v.name}', '${v.address}', '${v.contact}')">Edit</button>
                    <button class="btn-danger-small" onclick="deleteVendor(${v.id})">Delete</button>
                </td>
            </tr>
        `;
    });
}

function openAddVendor() {
    const name = prompt("Vendor Name:");
    if (!name) return;

    const address = prompt("Vendor Address:") || "";
    const contact = prompt("Vendor Contact:") || "";

    fetch("/api/vendors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, address, contact })
    }).then(() => loadVendors());
}

function editVendor(id, name, address, contact) {
    const newName = prompt("Vendor Name:", name);
    if (!newName) return;

    const newAddress = prompt("Vendor Address:", address) || "";
    const newContact = prompt("Vendor Contact:", contact) || "";

    fetch(`/api/vendors/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            name: newName,
            address: newAddress,
            contact: newContact
        })
    }).then(() => loadVendors());
}

function deleteVendor(id) {
    if (!confirm("Delete this vendor?")) return;

    fetch(`/api/vendors/${id}`, { method: "DELETE" })
        .then(() => loadVendors());
}



// ===============================
// HST / GST NUMBERS
// ===============================
async function loadHstNumbers() {
    const res = await fetch("/api/settings/hst-gst");
    const data = await res.json();

    const table = document.getElementById("hstTable");
    table.innerHTML = "";

    const number = data.default_hst_gst;

    table.innerHTML += `
        <tr>
            <td>${number}</td>
            <td>
                <button class="btn-small" onclick="editHst('${number}')">Edit</button>
                <button class="btn-danger-small" onclick="deleteHst('${number}')">Delete</button>
            </td>
        </tr>
    `;
}

function openAddHst() {
    const number = prompt("Enter new HST/GST number:");
    if (!number) return;

    fetch("/api/hst-gst", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ number })
    }).then(() => loadHstNumbers());
}

function editHst(oldNumber) {
    const newNumber = prompt("Edit HST/GST number:", oldNumber);
    if (!newNumber) return;

    fetch("/api/hst-gst", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ number: newNumber })
    }).then(() => loadHstNumbers());
}

function deleteHst(number) {
    if (!confirm("Delete this HST/GST number?")) return;

    // Reset to blank
    fetch("/api/hst-gst", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hst_gst_number: "" })
    }).then(() => loadHstNumbers());
}



// ===============================
// SIGNATURES
// ===============================
async function loadSignatures() {
    const res = await fetch("/api/signatures");
    const signatures = await res.json();

    const table = document.getElementById("signatureTable");
    table.innerHTML = "";

    signatures.forEach(sig => {
        table.innerHTML += `
            <tr>
                <td><img src="/signatures/${sig.image_path}" style="height:60px;"></td>
                <td>${sig.name}</td>
                <td>${sig.position}</td>
                <td>
                    <button class="btn-small" onclick="editSignature(${sig.id}, '${sig.name}', '${sig.position}')">Edit</button>
                    <button class="btn-danger-small" onclick="deleteSignature(${sig.id})">Delete</button>
                </td>
            </tr>
        `;
    });
}

function openAddSignature() {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/*";

    fileInput.onchange = async () => {
        const file = fileInput.files[0];
        if (!file) return;

        const name = prompt("Signature Name:") || "Unknown";
        const position = prompt("Position:") || "";

        const formData = new FormData();
        formData.append("signature", file);
        formData.append("name", name);
        formData.append("position", position);

        await fetch("/api/signatures/upload", {
            method: "POST",
            body: formData
        });

        loadSignatures();
    };

    fileInput.click();
}

function editSignature(id, name, position) {
    const newName = prompt("Edit Name:", name) || name;
    const newPosition = prompt("Edit Position:", position) || position;

    fetch(`/api/signatures/${id}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName, position: newPosition })
    }).then(() => loadSignatures());
}

function deleteSignature(id) {
    if (!confirm("Delete this signature?")) return;

    fetch(`/api/signatures/${id}/delete`, { method: "DELETE" })
        .then(() => loadSignatures());
}

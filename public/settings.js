document.addEventListener('DOMContentLoaded', loadSettings);

let currentLogoURL = null; // stores "/logo.png"

async function loadSettings() {
    try {
        const response = await fetch('/api/settings/company');
        const settings = await response.json();

        document.getElementById('company_name').value = settings.company_name || '';
        document.getElementById('company_address').value = settings.company_address || '';
        document.getElementById('company_phone').value = settings.company_phone || '';
        document.getElementById('default_shipping_method').value = settings.default_shipping_method || '';
        document.getElementById('default_shipping_terms').value = settings.default_shipping_terms || '';

        // Load logo preview
        if (settings.default_logo_url) {
            currentLogoURL = settings.default_logo_url; // "/logo.png"
            document.getElementById('logoPreview').style.display = 'block';
            document.getElementById('logoImage').src = currentLogoURL;
        }

    } catch (err) {
        console.error("Failed to load settings:", err);
    }
}

async function saveSettings() {
    const data = {
        company_name: document.getElementById('company_name').value,
        company_address: document.getElementById('company_address').value,
        company_phone: document.getElementById('company_phone').value,
        default_shipping_method: document.getElementById('default_shipping_method').value,
        default_shipping_terms: document.getElementById('default_shipping_terms').value,
        default_logo_path: currentLogoURL // IMPORTANT
    };

    try {
        const response = await fetch('/api/settings/company', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();
        alert(result.message || "Settings saved");

    } catch (err) {
        alert("Error saving settings: " + err.message);
    }
}

async function uploadLogo() {
    const fileInput = document.getElementById('logoUpload');
    if (!fileInput.files.length) {
        alert("Select a logo first");
        return;
    }

    const formData = new FormData();
    formData.append('logo', fileInput.files[0]);

    try {
        const response = await fetch('/api/settings/logo', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            currentLogoURL = result.logo_url; // "/logo.png"

            document.getElementById('logoPreview').style.display = 'block';
            document.getElementById('logoImage').src = currentLogoURL;

            alert("Logo uploaded successfully");
        } else {
            alert(result.error || "Upload failed");
        }

    } catch (err) {
        alert("Error uploading logo: " + err.message);
    }
}

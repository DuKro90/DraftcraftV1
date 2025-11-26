# 🔗 Frontend Integration Guide - DraftCraft Backend API

Complete guide for integrating the DraftCraft frontend with the production backend API.

---

## 📋 Overview

This guide covers:
1. **Setting up API authentication** (token-based)
2. **Connecting frontend to backend endpoints**
3. **Handling document uploads**
4. **Displaying extraction results**
5. **Generating and downloading proposals**
6. **Error handling and user feedback**

---

## 🔐 Authentication Setup

### Getting an API Token

**Endpoint:** `POST /api/auth/token/`

```javascript
async function getAuthToken(username, password) {
    const response = await fetch('http://localhost:8000/api/auth/token/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password,
        })
    });

    if (!response.ok) {
        throw new Error('Authentication failed');
    }

    const data = await response.json();
    return data.token; // Save this token for all subsequent requests
}

// Usage
const token = await getAuthToken('admin', 'password');
localStorage.setItem('authToken', token);
```

### Using Token in API Calls

```javascript
const token = localStorage.getItem('authToken');

const headers = {
    'Authorization': `Token ${token}`,
    'Content-Type': 'application/json',
};

fetch('http://localhost:8000/api/v1/documents/', {
    method: 'GET',
    headers: headers,
});
```

---

## 📤 Document Upload

### Upload a Document

**Endpoint:** `POST /api/v1/documents/`

```javascript
async function uploadDocument(file) {
    const token = localStorage.getItem('authToken');
    const formData = new FormData();
    formData.append('file', file);
    // Optional: append('document_type', 'pdf');

    const response = await fetch('http://localhost:8000/api/v1/documents/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
        },
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    const data = await response.json();
    return data; // Returns: { id, status: 'uploaded', original_filename, ... }
}

// HTML Usage
document.getElementById('fileInput').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    try {
        const doc = await uploadDocument(file);
        console.log('Document uploaded:', doc.id);
        await processDocument(doc.id);
    } catch (error) {
        alert('Error: ' + error.message);
    }
});
```

---

## ⚙️ Process Documents (OCR + NER)

### Trigger Document Processing

**Endpoint:** `POST /api/v1/documents/{id}/process/`

```javascript
async function processDocument(documentId) {
    const token = localStorage.getItem('authToken');

    const response = await fetch(
        `http://localhost:8000/api/v1/documents/${documentId}/process/`,
        {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json',
            },
        }
    );

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing failed');
    }

    const data = await response.json();
    console.log('Processing complete:', data.status);
    return data;
}
```

### Get Extraction Results

**Endpoint:** `GET /api/v1/documents/{id}/extraction_summary/`

```javascript
async function getExtractionResults(documentId) {
    const token = localStorage.getItem('authToken');

    const response = await fetch(
        `http://localhost:8000/api/v1/documents/${documentId}/extraction_summary/`,
        {
            headers: {
                'Authorization': `Token ${token}`,
            },
        }
    );

    if (!response.ok) {
        throw new Error('Failed to get extraction results');
    }

    const data = await response.json();
    // Returns: {
    //   document_id, status, ocr_confidence, entity_count,
    //   entity_types, materials_found, processing_time_ms, ...
    // }
    return data;
}
```

---

## 📋 Generate Proposals

### Create a Proposal

**Endpoint:** `POST /api/v1/proposals/`

```javascript
async function generateProposal(documentId, customerInfo) {
    const token = localStorage.getItem('authToken');

    const response = await fetch('http://localhost:8000/api/v1/proposals/', {
        method: 'POST',
        headers: {
            'Authorization': `Token ${token}`,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            document_id: documentId,
            template_id: null, // Optional: use default template
            customer_name: customerInfo.name,
            customer_email: customerInfo.email,
            customer_address: customerInfo.address || '',
            valid_days: 30,
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Proposal generation failed');
    }

    const data = await response.json();
    // Returns: { id, proposal_number, status, total, lines: [...], ... }
    return data;
}

// Usage
const proposal = await generateProposal('doc-uuid', {
    name: 'Max Mustermann',
    email: 'max@example.de',
    address: 'Musterstraße 1, 12345 Musterstadt'
});

console.log('Proposal created:', proposal.proposal_number);
```

### Download Proposal as PDF

**Endpoint:** `GET /api/v1/proposals/{id}/download_pdf/`

```javascript
async function downloadProposalPdf(proposalId) {
    const token = localStorage.getItem('authToken');

    const response = await fetch(
        `http://localhost:8000/api/v1/proposals/${proposalId}/download_pdf/`,
        {
            headers: {
                'Authorization': `Token ${token}`,
            },
        }
    );

    if (!response.ok) {
        throw new Error('PDF download failed');
    }

    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = 'proposal.pdf';
    if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
    }

    // Download the PDF
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Usage
document.getElementById('downloadBtn').addEventListener('click', async () => {
    try {
        await downloadProposalPdf(proposalId);
    } catch (error) {
        alert('Error: ' + error.message);
    }
});
```

### Send Proposal via Email

**Endpoint:** `POST /api/v1/proposals/{id}/send/`

```javascript
async function sendProposalEmail(proposalId, recipientEmail) {
    const token = localStorage.getItem('authToken');

    const response = await fetch(
        `http://localhost:8000/api/v1/proposals/${proposalId}/send/`,
        {
            method: 'POST',
            headers: {
                'Authorization': `Token ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                recipient_email: recipientEmail,
                message: 'Please find attached your proposal.',
            }),
        }
    );

    if (!response.ok) {
        throw new Error('Failed to send proposal');
    }

    const data = await response.json();
    console.log(data.detail); // "Proposal sent successfully"
    return data;
}
```

---

## 📊 API Client Helper Class

Create a reusable API client class:

```javascript
class DraftCraftAPI {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('authToken');
    }

    setToken(token) {
        this.token = token;
        localStorage.setItem('authToken', token);
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const headers = {
            ...options.headers,
        };

        if (this.token && !options.skipAuth) {
            headers['Authorization'] = `Token ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response;
    }

    // Authentication
    async authenticate(username, password) {
        const response = await this.request('/api/auth/token/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            skipAuth: true,
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        this.setToken(data.token);
        return data;
    }

    // Documents
    async uploadDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await this.request('/api/v1/documents/', {
            method: 'POST',
            body: formData,
        });

        return response.json();
    }

    async getDocument(documentId) {
        const response = await this.request(`/api/v1/documents/${documentId}/`);
        return response.json();
    }

    async processDocument(documentId) {
        const response = await this.request(
            `/api/v1/documents/${documentId}/process/`,
            { method: 'POST', headers: { 'Content-Type': 'application/json' } }
        );
        return response.json();
    }

    async getExtractionResults(documentId) {
        const response = await this.request(
            `/api/v1/documents/${documentId}/extraction_summary/`
        );
        return response.json();
    }

    // Proposals
    async generateProposal(proposalData) {
        const response = await this.request('/api/v1/proposals/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(proposalData),
        });

        return response.json();
    }

    async getProposal(proposalId) {
        const response = await this.request(`/api/v1/proposals/${proposalId}/`);
        return response.json();
    }

    async downloadProposalPdf(proposalId) {
        const response = await this.request(
            `/api/v1/proposals/${proposalId}/download_pdf/`
        );
        return response.blob();
    }

    async sendProposal(proposalId, email) {
        const response = await this.request(
            `/api/v1/proposals/${proposalId}/send/`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient_email: email }),
            }
        );

        return response.json();
    }
}

// Usage
const api = new DraftCraftAPI();

// Authenticate
await api.authenticate('admin', 'password');

// Upload and process document
const doc = await api.uploadDocument(fileInput.files[0]);
await api.processDocument(doc.id);

// Generate proposal
const proposal = await api.generateProposal({
    document_id: doc.id,
    customer_name: 'John Doe',
    customer_email: 'john@example.com',
    valid_days: 30,
});

// Download PDF
const pdfBlob = await api.downloadProposalPdf(proposal.id);
```

---

## 🎨 Frontend HTML Structure

Example HTML structure to work with the API client:

```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DraftCraft - Angebotsverwaltung</title>
    <link rel="stylesheet" href="style.css">
</head>
<body class="theme-copper">
    <main>
        <!-- Upload Section -->
        <section id="uploadSection">
            <h2>Dokument hochladen</h2>
            <input type="file" id="fileInput" accept=".pdf,.txt,.png,.jpg">
            <button onclick="handleUpload()">Hochladen</button>
            <div id="uploadStatus"></div>
        </section>

        <!-- Processing Section -->
        <section id="processingSection" style="display:none;">
            <h2>Verarbeitung läuft...</h2>
            <div id="processingStatus"></div>
            <div id="extractionResults"></div>
        </section>

        <!-- Proposal Section -->
        <section id="proposalSection" style="display:none;">
            <h2>Angebot erstellen</h2>
            <form id="proposalForm">
                <input type="text" id="customerName" placeholder="Kundenname" required>
                <input type="email" id="customerEmail" placeholder="E-Mail" required>
                <textarea id="customerAddress" placeholder="Adresse"></textarea>
                <button type="submit">Angebot generieren</button>
            </form>
            <div id="proposalResult"></div>
        </section>
    </main>

    <script src="api-client.js"></script>
    <script src="app.js"></script>
</body>
</html>
```

---

## 🚀 Complete Integration Example

Here's a complete workflow:

```javascript
// app.js - Complete integration example

const api = new DraftCraftAPI('http://localhost:8000');
let currentDocumentId = null;
let currentProposalId = null;

// Initialize
async function init() {
    try {
        // Check if already authenticated
        if (!api.token) {
            const username = prompt('Username:');
            const password = prompt('Password:');
            await api.authenticate(username, password);
        }
        enableUpload();
    } catch (error) {
        alert('Authentication error: ' + error.message);
    }
}

// Step 1: Upload Document
async function handleUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Bitte eine Datei auswählen');
        return;
    }

    try {
        updateStatus('Hochladen...');
        const doc = await api.uploadDocument(file);
        currentDocumentId = doc.id;

        updateStatus('Dokument hochgeladen. Verarbeitung wird gestartet...');
        await api.processDocument(doc.id);

        updateStatus('Verarbeitung abgeschlossen!');
        showExtractionResults();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Step 2: Show Extraction Results
async function showExtractionResults() {
    try {
        const results = await api.getExtractionResults(currentDocumentId);

        const html = `
            <div class="extraction-summary">
                <h3>Erkannte Entitäten</h3>
                <p>Vertrauen (OCR): ${(results.ocr_confidence * 100).toFixed(1)}%</p>
                <p>Entitäten gefunden: ${results.entity_count}</p>
                <p>Zeitaufwand: ${results.processing_time_ms}ms</p>
                <pre>${JSON.stringify(results.entity_types, null, 2)}</pre>
            </div>
        `;

        document.getElementById('extractionResults').innerHTML = html;
        document.getElementById('proposalSection').style.display = 'block';
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Step 3: Generate Proposal
document.getElementById('proposalForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    try {
        updateStatus('Angebot wird generiert...');

        const proposal = await api.generateProposal({
            document_id: currentDocumentId,
            customer_name: document.getElementById('customerName').value,
            customer_email: document.getElementById('customerEmail').value,
            customer_address: document.getElementById('customerAddress').value,
            valid_days: 30,
        });

        currentProposalId = proposal.id;

        const html = `
            <div class="proposal-success">
                <h3>Angebot erstellt!</h3>
                <p>Angebotsnummer: <strong>${proposal.proposal_number}</strong></p>
                <p>Gesamtbetrag: <strong>${proposal.total} €</strong></p>
                <button onclick="downloadPDF()">PDF herunterladen</button>
                <button onclick="sendEmail()">Per E-Mail versenden</button>
            </div>
        `;

        document.getElementById('proposalResult').innerHTML = html;
        updateStatus('Angebot erfolgreich erstellt!');
    } catch (error) {
        alert('Error: ' + error.message);
    }
});

// Step 4: Download PDF
async function downloadPDF() {
    try {
        const blob = await api.downloadProposalPdf(currentProposalId);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'proposal.pdf';
        a.click();
        URL.revokeObjectURL(url);
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Step 5: Send Email
async function sendEmail() {
    try {
        const email = prompt('E-Mail-Adresse:');
        if (email) {
            await api.sendProposal(currentProposalId, email);
            alert('Angebot erfolgreich versendet!');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Helper functions
function updateStatus(message) {
    document.getElementById('uploadStatus').textContent = message;
}

function enableUpload() {
    document.getElementById('uploadSection').style.display = 'block';
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', init);
```

---

## 🌐 CORS Configuration

The backend is configured to allow CORS from:
- `http://localhost:3000`
- `http://localhost:8000`
- `http://localhost:5173` (Vite dev server)

If deploying frontend elsewhere, update the `CORS_ALLOWED_ORIGINS` in backend `.env`:

```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.com,https://your-app.com
```

---

## ⚠️ Error Handling

Always wrap API calls in try-catch:

```javascript
try {
    const result = await api.uploadDocument(file);
} catch (error) {
    // Possible errors:
    // - Network error: fetch failed
    // - 401: Authentication failed (token expired)
    // - 400: Bad request (validation error)
    // - 404: Resource not found
    // - 500: Server error

    console.error('Error:', error.message);
    showUserError(error.message);
}
```

---

## 🧪 Testing the Integration

### 1. Test Authentication
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

### 2. Test Upload
```bash
curl -X POST http://localhost:8000/api/v1/documents/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "file=@testfile.pdf"
```

### 3. Test Processing
```bash
curl -X POST http://localhost:8000/api/v1/documents/{doc-id}/process/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### 4. Test Proposal Generation
```bash
curl -X POST http://localhost:8000/api/v1/proposals/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"document_id":"...", "customer_name":"Test", "customer_email":"test@example.com"}'
```

### 5. Test PDF Download
```bash
curl -X GET http://localhost:8000/api/v1/proposals/{proposal-id}/download_pdf/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -o proposal.pdf
```

---

## 📚 API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/auth/token/` | Get authentication token |
| POST | `/api/v1/documents/` | Upload document |
| GET | `/api/v1/documents/{id}/` | Get document |
| POST | `/api/v1/documents/{id}/process/` | Process document (OCR+NER) |
| GET | `/api/v1/documents/{id}/extraction_summary/` | Get extraction results |
| POST | `/api/v1/proposals/` | Create proposal |
| GET | `/api/v1/proposals/{id}/` | Get proposal |
| GET | `/api/v1/proposals/{id}/download_pdf/` | Download proposal as PDF |
| POST | `/api/v1/proposals/{id}/send/` | Send proposal via email |

---

## 🔗 Interactive API Documentation

Visit `http://localhost:8000/api/docs/swagger/` to test all endpoints directly in the browser with Swagger UI!

---

**Last Updated:** November 26, 2025
**Backend API Version:** 1.0
**Status:** Production Ready

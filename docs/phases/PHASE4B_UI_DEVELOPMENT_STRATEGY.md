# Phase 4B: UI Development Strategy - DraftCraft V1

**Version:** 1.0
**Created:** 2025-12-02
**Status:** 🎯 Planning - Best Practices for Easy-to-Use Interface

---

## 📋 Executive Summary

Based on environment analysis and existing codebase, this document outlines the **best practice approach** for developing a production-ready, easy-to-use user interface for the DraftCraft German Handwerk Document Analysis System.

**Key Findings:**
- ✅ **Backend:** Django 5.0 + DRF with comprehensive REST APIs
- ✅ **Database:** Supabase PostgreSQL (Production-ready with RLS)
- ✅ **Existing Frontend:** Basic HTML demo in `Frontend/` directory
- ✅ **Runtime:** Python 3.14 + Node.js v22.21 available
- ✅ **API Documentation:** Complete integration guide exists
- ✅ **Admin UI:** Django Admin with custom tooltips (production-ready)

---

## 🎯 Recommended UI Architecture

### Option 1: React + Vite (RECOMMENDED) ⭐

**Why React?**
- ✅ **Industry Standard** - Largest ecosystem, best hiring pool
- ✅ **TypeScript Support** - Type-safe integration with Django backend
- ✅ **Component Reusability** - Matches your German Handwerk domain models
- ✅ **Modern Tooling** - Vite for instant HMR (Hot Module Replacement)
- ✅ **Django Integration** - Well-established patterns with DRF
- ✅ **German i18n** - `react-i18next` for multilingual support

**Tech Stack:**
```bash
Frontend Framework:  React 18 + TypeScript
Build Tool:          Vite 5.x
UI Library:          shadcn/ui + Tailwind CSS (easy customization)
State Management:    TanStack Query (React Query) - perfect for REST APIs
Forms:               React Hook Form + Zod validation
Date/Numbers:        date-fns (German locale support)
Charts:              Recharts (for Betriebskennzahlen dashboards)
Deployment:          Google Cloud Run (same as Django backend)
```

**Project Structure:**
```
DraftcraftV1/
├── backend/                    # Existing Django backend
├── frontend/                   # NEW React application
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # shadcn/ui components (buttons, cards, forms)
│   │   │   ├── documents/     # Document upload, processing UI
│   │   │   ├── proposals/     # Proposal generation, PDF download
│   │   │   ├── admin/         # Pattern review, fix approval
│   │   │   └── dashboard/     # Analytics, metrics visualization
│   │   ├── lib/
│   │   │   ├── api/           # Type-safe API client for Django backend
│   │   │   ├── hooks/         # Custom React hooks (useDocuments, useProposals)
│   │   │   └── utils/         # German number/date formatting
│   │   ├── types/             # TypeScript types (auto-generated from Django models)
│   │   ├── pages/             # Main application pages
│   │   └── i18n/              # German translations
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── docker-compose.yml          # Updated to include frontend service
└── docs/phases/
    └── PHASE4B_UI_DEVELOPMENT_STRATEGY.md  # This file
```

---

### Option 2: Django Templates + HTMX (Alternative)

**When to Choose?**
- ✅ Single developer/small team
- ✅ Prefer server-side rendering
- ✅ Want to avoid JavaScript build complexity
- ✅ Django admin-like interface is acceptable

**Tech Stack:**
```bash
Template Engine:     Django Templates + Jinja2
Interactivity:       HTMX + Alpine.js
CSS Framework:       Tailwind CSS
Forms:               Django Forms (server-side validation)
```

**Pros:**
- Simpler deployment (single Django app)
- No Node.js build step required
- Better SEO out-of-the-box

**Cons:**
- Less interactive (no real-time updates without WebSockets)
- Limited component reusability
- Harder to scale UI complexity

---

## 🎨 "Easy to Use" Design Principles

Based on your existing demo (`Frontend/demo.html`) and tooltip system, here are the **core UX rules** for DraftCraft:

### 1. Progressive Disclosure (Step-by-Step Workflow)

**Principle:** Don't overwhelm users - show only what's needed at each step.

**Implementation:**
```typescript
// Example: Document Processing Workflow
Step 1: Upload Document    → Show file input + "Analyze" button
Step 2: Processing         → Show progress bar + live OCR preview
Step 3: Review Extractions → Show confidence scores + edit capabilities
Step 4: Generate Proposal  → Show customer form (pre-filled from extraction)
Step 5: Download/Send      → Show PDF preview + email options
```

**Visual Pattern:**
```
┌─────────────┐
│ 1. Upload   │ ✅ Complete
└─────────────┘
       ↓
┌─────────────┐
│ 2. Process  │ ⏳ In Progress...
└─────────────┘
       ↓
┌─────────────┐
│ 3. Review   │ ⏸️ Waiting (disabled until step 2 completes)
└─────────────┘
```

**Code Example (React):**
```tsx
// components/documents/DocumentWorkflow.tsx
const DocumentWorkflow = () => {
  const [currentStep, setCurrentStep] = useState<'upload' | 'process' | 'review' | 'proposal'>('upload');

  return (
    <div className="max-w-4xl mx-auto">
      <StepIndicator current={currentStep} />

      {currentStep === 'upload' && <UploadStep onComplete={() => setCurrentStep('process')} />}
      {currentStep === 'process' && <ProcessingStep onComplete={() => setCurrentStep('review')} />}
      {currentStep === 'review' && <ReviewStep onComplete={() => setCurrentStep('proposal')} />}
      {currentStep === 'proposal' && <ProposalStep />}
    </div>
  );
};
```

---

### 2. Contextual Help (Tooltips + Inline Validation)

**Principle:** Help users understand German Handwerk terminology without leaving the page.

**Implementation (inspired by your Django Admin tooltips):**

```tsx
// components/ui/FormField.tsx
interface FormFieldProps {
  label: string;
  helpText?: string;
  tier?: 'tier1' | 'tier2' | 'tier3' | 'critical' | 'dsgvo';
  icon?: '💡' | '✓' | '⚠';
  children: React.ReactNode;
}

const FormField = ({ label, helpText, tier = 'tier1', icon, children }: FormFieldProps) => {
  const borderColors = {
    tier1: 'border-l-blue-500',      // Global standards
    tier2: 'border-l-orange-500',    // Company metrics
    tier3: 'border-l-purple-500',    // Dynamic adjustments
    critical: 'border-l-red-500',    // Critical fields
    dsgvo: 'border-l-green-500',     // DSGVO compliance
  };

  return (
    <div className="mb-4">
      <label className="block font-semibold text-gray-700 mb-1">{label}</label>
      {children}
      {helpText && (
        <div className={`mt-2 p-3 bg-gray-50 border-l-4 ${borderColors[tier]} rounded text-sm text-gray-600 hover:bg-blue-50 transition-colors`}>
          {icon && <span className="mr-2">{icon}</span>}
          {helpText}
        </div>
      )}
    </div>
  );
};

// Usage:
<FormField
  label="Holzart (Wood Type)"
  tier="tier1"
  helpText='Wood type name (e.g., "Eiche", "Buche", "Kiefer")'
>
  <Input placeholder="Eiche" />
</FormField>

<FormField
  label="Stundensatz Arbeit (Labor Rate)"
  tier="tier2"
  helpText="Labor rate per hour in EUR (e.g., 65.00 for skilled carpenter)"
>
  <Input type="number" placeholder="65.00" />
</FormField>
```

---

### 3. Smart Defaults (Pre-fill from AI Extraction)

**Principle:** Minimize manual data entry by using OCR/NER results.

**Implementation:**
```tsx
// hooks/useSmartDefaults.ts
const useSmartDefaults = (documentId: string) => {
  const { data: extraction } = useQuery({
    queryKey: ['extraction', documentId],
    queryFn: () => api.getExtractionResults(documentId),
  });

  // Auto-fill customer form from extracted entities
  const customerDefaults = useMemo(() => ({
    name: extraction?.entities.find(e => e.entity_type === 'CUSTOMER_NAME')?.value || '',
    email: extraction?.entities.find(e => e.entity_type === 'EMAIL')?.value || '',
    address: extraction?.entities.find(e => e.entity_type === 'ADDRESS')?.value || '',
  }), [extraction]);

  return { customerDefaults, extraction };
};

// Usage in ProposalForm:
const ProposalForm = ({ documentId }: { documentId: string }) => {
  const { customerDefaults } = useSmartDefaults(documentId);
  const form = useForm({ defaultValues: customerDefaults });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <FormField label="Kundenname" helpText="Automatically extracted from document">
        <Input {...form.register('name')} />
        {customerDefaults.name && <span className="text-xs text-green-600">✓ Auto-filled</span>}
      </FormField>
      {/* ... */}
    </form>
  );
};
```

---

### 4. Visual Feedback (Loading States + Confidence Indicators)

**Principle:** Always show system status and data quality.

**Implementation:**
```tsx
// components/documents/ExtractionConfidence.tsx
const ExtractionConfidence = ({ confidence }: { confidence: number }) => {
  const getColor = (score: number) => {
    if (score >= 0.92) return 'bg-green-500';     // AUTO_ACCEPT
    if (score >= 0.80) return 'bg-blue-500';      // AGENT_VERIFY
    if (score >= 0.70) return 'bg-yellow-500';    // AGENT_EXTRACT
    return 'bg-red-500';                          // HUMAN_REVIEW
  };

  const getLabel = (score: number) => {
    if (score >= 0.92) return 'Excellent';
    if (score >= 0.80) return 'Good';
    if (score >= 0.70) return 'Fair';
    return 'Needs Review';
  };

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${getColor(confidence)}`}
          style={{ width: `${confidence * 100}%` }}
        />
      </div>
      <span className="text-sm font-medium">{(confidence * 100).toFixed(1)}%</span>
      <span className="text-xs text-gray-500">{getLabel(confidence)}</span>
    </div>
  );
};
```

---

### 5. German Locale Support (Numbers, Dates, Currency)

**Principle:** Use German formatting conventions throughout.

**Implementation:**
```typescript
// lib/utils/formatters.ts
import { format } from 'date-fns';
import { de } from 'date-fns/locale';

// German number format: 1.234,56
export const formatGermanNumber = (num: number, decimals = 2): string => {
  return new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(num);
};

// German currency: 2.450,80 €
export const formatGermanCurrency = (amount: number): string => {
  return new Intl.NumberFormat('de-DE', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount);
};

// German date: 15.11.2024
export const formatGermanDate = (date: Date): string => {
  return format(date, 'dd.MM.yyyy', { locale: de });
};

// Usage in components:
<div>
  <p>Gesamtbetrag: {formatGermanCurrency(2450.80)}</p>
  <p>Datum: {formatGermanDate(new Date())}</p>
  <p>Menge: {formatGermanNumber(25.5)} m²</p>
</div>
```

---

### 6. Keyboard Navigation (Accessibility)

**Principle:** Power users should be able to complete workflows without mouse.

**Implementation:**
```tsx
// Keyboard shortcuts
const useKeyboardShortcuts = () => {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Ctrl+U: Upload document
      if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        document.getElementById('fileInput')?.click();
      }

      // Ctrl+Enter: Submit current form
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault();
        document.querySelector('form')?.requestSubmit();
      }

      // Escape: Close modal
      if (e.key === 'Escape') {
        setModalOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);
};
```

---

### 7. Error Recovery (Graceful Degradation)

**Principle:** Never lose user data - always provide recovery options.

**Implementation:**
```tsx
// hooks/useAutosave.ts
const useAutosave = <T extends Record<string, any>>(key: string, data: T) => {
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      localStorage.setItem(`autosave_${key}`, JSON.stringify(data));
    }, 1000); // Debounce 1 second

    return () => clearTimeout(timeoutId);
  }, [key, data]);

  const restore = useCallback(() => {
    const saved = localStorage.getItem(`autosave_${key}`);
    return saved ? JSON.parse(saved) : null;
  }, [key]);

  return { restore };
};

// Usage:
const ProposalForm = () => {
  const [formData, setFormData] = useState({});
  const { restore } = useAutosave('proposal_form', formData);

  useEffect(() => {
    const restored = restore();
    if (restored) {
      const shouldRestore = window.confirm('Unsaved draft found. Restore?');
      if (shouldRestore) setFormData(restored);
    }
  }, []);

  // ...
};
```

---

## 🚀 Quick Start Guide (React + Vite)

### Step 1: Initialize React Project

```bash
cd C:\Codes\DraftcraftV1

# Create new Vite project
npm create vite@latest frontend -- --template react-ts
cd frontend

# Install dependencies
npm install

# Install UI libraries
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-label
npm install tailwindcss postcss autoprefixer
npm install @tanstack/react-query axios
npm install react-hook-form @hookform/resolvers zod
npm install date-fns recharts
npm install react-i18next i18next

# Install dev dependencies
npm install -D @types/node
```

### Step 2: Configure Tailwind CSS

```bash
npx tailwindcss init -p
```

Update `tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // DraftCraft Brand Colors (from demo.html)
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
        accent: {
          500: '#F5C400', // Yellow theme
        },
      },
    },
  },
  plugins: [],
}
```

### Step 3: Create Type-Safe API Client

```typescript
// src/lib/api/client.ts
import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class DraftCraftAPI {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Interceptor: Add auth token
    this.client.interceptors.request.use((config) => {
      const token = localStorage.getItem('authToken');
      if (token) {
        config.headers.Authorization = `Token ${token}`;
      }
      return config;
    });

    // Interceptor: Handle 401 (redirect to login)
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('authToken');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async authenticate(username: string, password: string) {
    const { data } = await this.client.post('/api/auth/token/', { username, password });
    localStorage.setItem('authToken', data.token);
    return data;
  }

  // Documents
  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await this.client.post('/api/v1/documents/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  }

  async processDocument(documentId: string) {
    const { data } = await this.client.post(`/api/v1/documents/${documentId}/process/`);
    return data;
  }

  async getExtractionResults(documentId: string) {
    const { data } = await this.client.get(`/api/v1/documents/${documentId}/extraction_summary/`);
    return data;
  }

  // Proposals
  async generateProposal(proposalData: {
    document_id: string;
    customer_name: string;
    customer_email: string;
    customer_address?: string;
    valid_days?: number;
  }) {
    const { data } = await this.client.post('/api/v1/proposals/', proposalData);
    return data;
  }

  async downloadProposalPdf(proposalId: string): Promise<Blob> {
    const { data } = await this.client.get(`/api/v1/proposals/${proposalId}/download_pdf/`, {
      responseType: 'blob',
    });
    return data;
  }
}

export const api = new DraftCraftAPI();
```

### Step 4: Setup React Query

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
);
```

### Step 5: Create Main Workflow Component

```tsx
// src/pages/DocumentWorkflow.tsx
import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { formatGermanCurrency, formatGermanDate } from '@/lib/utils/formatters';

export default function DocumentWorkflow() {
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<'upload' | 'process' | 'review' | 'proposal'>('upload');

  // Step 1: Upload
  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadDocument(file),
    onSuccess: (data) => {
      setDocumentId(data.id);
      setCurrentStep('process');
      processMutation.mutate(data.id);
    },
  });

  // Step 2: Process
  const processMutation = useMutation({
    mutationFn: (docId: string) => api.processDocument(docId),
    onSuccess: () => {
      setCurrentStep('review');
    },
  });

  // Step 3: Review (auto-fetch extraction results)
  const { data: extractionData, isLoading: isLoadingExtraction } = useQuery({
    queryKey: ['extraction', documentId],
    queryFn: () => api.getExtractionResults(documentId!),
    enabled: !!documentId && currentStep === 'review',
  });

  // Step 4: Generate Proposal
  const proposalMutation = useMutation({
    mutationFn: (proposalData: any) => api.generateProposal(proposalData),
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      uploadMutation.mutate(file);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Angebots-Workflow</h1>

      {/* Step Indicator */}
      <div className="flex items-center justify-between mb-8">
        {['upload', 'process', 'review', 'proposal'].map((step, idx) => (
          <div key={step} className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center ${
                currentStep === step ? 'bg-blue-500 text-white' : 'bg-gray-200'
              }`}
            >
              {idx + 1}
            </div>
            {idx < 3 && <div className="w-20 h-1 bg-gray-200 mx-2" />}
          </div>
        ))}
      </div>

      {/* Step 1: Upload */}
      {currentStep === 'upload' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">1. Dokument hochladen</h2>
          <input
            type="file"
            onChange={handleFileUpload}
            accept=".pdf,.png,.jpg,.jpeg"
            className="block w-full border p-2 rounded"
            disabled={uploadMutation.isPending}
          />
          {uploadMutation.isPending && <p className="mt-2 text-blue-600">Hochladen...</p>}
        </div>
      )}

      {/* Step 2: Processing */}
      {currentStep === 'process' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">2. Verarbeitung läuft...</h2>
          <div className="animate-pulse">OCR + NER Extraktion wird durchgeführt...</div>
        </div>
      )}

      {/* Step 3: Review */}
      {currentStep === 'review' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">3. Ergebnisse prüfen</h2>
          {isLoadingExtraction ? (
            <p>Laden...</p>
          ) : (
            <>
              <p>Vertrauen (OCR): {(extractionData.ocr_confidence * 100).toFixed(1)}%</p>
              <p>Entitäten gefunden: {extractionData.entity_count}</p>
              <button
                onClick={() => setCurrentStep('proposal')}
                className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Weiter zu Angebot
              </button>
            </>
          )}
        </div>
      )}

      {/* Step 4: Proposal */}
      {currentStep === 'proposal' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">4. Angebot erstellen</h2>
          {/* Add form here */}
        </div>
      )}
    </div>
  );
}
```

---

## 📦 Docker Integration

Update `docker-compose.yml` to include frontend:

```yaml
version: '3.9'

services:
  backend:
    build:
      context: ./backend
      dockerfile: ../Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: draftcraft_dev
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
```

Frontend `Dockerfile`:
```dockerfile
FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

---

## 🧪 Testing Strategy

### Unit Tests (Vitest)

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom
```

```typescript
// src/lib/utils/formatters.test.ts
import { describe, it, expect } from 'vitest';
import { formatGermanCurrency, formatGermanNumber } from './formatters';

describe('German Formatters', () => {
  it('formats currency correctly', () => {
    expect(formatGermanCurrency(2450.80)).toBe('2.450,80 €');
    expect(formatGermanCurrency(1234567.89)).toBe('1.234.567,89 €');
  });

  it('formats numbers correctly', () => {
    expect(formatGermanNumber(25.5, 1)).toBe('25,5');
    expect(formatGermanNumber(1234.567, 2)).toBe('1.234,57');
  });
});
```

### E2E Tests (Playwright)

```bash
npm install -D @playwright/test
```

```typescript
// e2e/document-workflow.spec.ts
import { test, expect } from '@playwright/test';

test('complete document workflow', async ({ page }) => {
  // 1. Upload document
  await page.goto('http://localhost:5173');
  await page.setInputFiles('input[type="file"]', 'test-invoice.pdf');
  await page.click('button:has-text("Analysieren")');

  // 2. Wait for processing
  await expect(page.locator('text=Verarbeitung läuft')).toBeVisible();
  await expect(page.locator('text=Ergebnisse prüfen')).toBeVisible({ timeout: 30000 });

  // 3. Review results
  await expect(page.locator('text=Vertrauen (OCR)')).toBeVisible();
  await page.click('button:has-text("Weiter zu Angebot")');

  // 4. Generate proposal
  await page.fill('input[name="customer_name"]', 'Test GmbH');
  await page.fill('input[name="customer_email"]', 'test@example.de');
  await page.click('button:has-text("Generieren")');

  await expect(page.locator('text=Angebot erfolgreich erstellt')).toBeVisible();
});
```

---

## 📊 Performance Optimization

### 1. Code Splitting

```typescript
// src/App.tsx
import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

const DocumentWorkflow = lazy(() => import('./pages/DocumentWorkflow'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Laden...</div>}>
        <Routes>
          <Route path="/" element={<DocumentWorkflow />} />
          <Route path="/admin" element={<AdminDashboard />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### 2. Image Optimization

```bash
npm install -D vite-plugin-imagemin
```

### 3. Bundle Analysis

```bash
npm install -D rollup-plugin-visualizer
npm run build
npm run preview
```

---

## 🚢 Deployment (Google Cloud Run)

### Build Production Image

```dockerfile
# frontend/Dockerfile.production
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Deploy to Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/draftcraft-frontend

# Deploy
gcloud run deploy draftcraft-frontend \
  --image gcr.io/PROJECT_ID/draftcraft-frontend \
  --platform managed \
  --region europe-west3 \
  --allow-unauthenticated \
  --set-env-vars VITE_API_URL=https://backend-url.run.app
```

---

## 📋 Implementation Checklist

### Phase 4B.1: Core UI Setup (Week 1)
- [ ] Initialize React + Vite project
- [ ] Setup Tailwind CSS + shadcn/ui
- [ ] Configure TypeScript types
- [ ] Create API client with authentication
- [ ] Setup React Query for data fetching
- [ ] Implement German formatters (numbers, dates, currency)

### Phase 4B.2: Document Workflow (Week 2)
- [ ] Upload component with drag-and-drop
- [ ] Processing status with live progress
- [ ] Extraction results display with confidence scores
- [ ] Entity review/edit interface
- [ ] Auto-fill customer form

### Phase 4B.3: Proposal Generation (Week 3)
- [ ] Customer form with validation
- [ ] Proposal line items editor
- [ ] PDF preview component
- [ ] Download PDF functionality
- [ ] Email sending interface

### Phase 4B.4: Admin Dashboard (Week 4)
- [ ] Pattern review interface
- [ ] Fix approval workflow
- [ ] Deployment management UI
- [ ] Analytics charts (Recharts)
- [ ] Betriebskennzahlen visualization

### Phase 4B.5: Testing & Polish (Week 5)
- [ ] Unit tests for utilities
- [ ] E2E tests for critical workflows
- [ ] Performance optimization
- [ ] Accessibility audit
- [ ] German i18n review

### Phase 4B.6: Deployment (Week 6)
- [ ] Production build optimization
- [ ] Docker integration
- [ ] Google Cloud Run deployment
- [ ] SSL/HTTPS configuration
- [ ] Load testing

---

## 🎯 Success Metrics

**User Experience:**
- ✅ Document processing workflow: < 3 clicks from upload to proposal
- ✅ Page load time: < 2 seconds (LCP)
- ✅ Time to Interactive: < 3 seconds
- ✅ Accessibility score: ≥ 90 (Lighthouse)

**Technical:**
- ✅ Test coverage: ≥ 80%
- ✅ Bundle size: < 500KB (gzipped)
- ✅ TypeScript: Strict mode enabled, 0 `any` types
- ✅ Responsive: Mobile (360px) to Desktop (1920px)

---

## 📚 Resources

**Documentation:**
- [React 18 Docs](https://react.dev)
- [Vite Guide](https://vitejs.dev/guide/)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [React Hook Form](https://react-hook-form.com/)

**Existing Codebase:**
- `FRONTEND_INTEGRATION_GUIDE.md` - Backend API documentation
- `backend/ADMIN_TOOLTIPS_GUIDE.md` - Tooltip design patterns
- `Frontend/demo.html` - Current UI prototype

---

**Last Updated:** 2025-12-02
**Status:** 🎯 Ready for Implementation
**Next Steps:** Review with team, initialize React project, start Phase 4B.1

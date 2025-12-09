# DraftCraft Frontend

Modern React + TypeScript frontend for the German Handwerk Document Analysis System.

## 🚀 Quick Start

### Prerequisites

- Node.js v22+ (already installed)
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

## 📁 Project Structure

```
frontend_new/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── ui/           # Base components (Button, Input, Card, etc.)
│   │   ├── documents/    # Document-related components
│   │   └── proposals/    # Proposal-related components
│   ├── lib/
│   │   ├── api/          # API client and utilities
│   │   ├── hooks/        # Custom React hooks
│   │   └── utils/        # Utility functions (formatters, etc.)
│   ├── pages/            # Page components
│   ├── types/            # TypeScript type definitions
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles
├── public/               # Static assets
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── tailwind.config.js    # Tailwind CSS configuration
```

## 🎨 Key Features

### 1. Easy-to-Use Workflow
- **Step-by-step interface**: Upload → Process → Review → Proposal
- **Visual progress indicators**: Always know where you are
- **Smart defaults**: Auto-fill customer data from extracted entities

### 2. German Handwerk Support
- German number formatting (1.234,56)
- German currency (2.450,80 €)
- German date formatting (15.11.2024)
- TIER 1/2/3 color-coded tooltips

### 3. Type-Safe API Integration
- Full TypeScript types for Django REST API
- React Query for efficient data fetching
- Automatic retry and error handling
- Optimistic UI updates

### 4. Accessibility
- Keyboard navigation support
- ARIA labels and semantic HTML
- Focus management
- Screen reader friendly

## 🛠️ Development Scripts

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test

# Run E2E tests
npm run test:e2e

# Lint code
npm run lint

# Format code
npm run format
```

## 📚 Component Library

### Base Components

```tsx
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Card from '@/components/ui/Card'
import FormField from '@/components/ui/FormField'

// Button with variants
<Button variant="primary" size="md" isLoading={false}>
  Click Me
</Button>

// Input with error handling
<Input
  type="text"
  placeholder="Enter text"
  error="This field is required"
/>

// Card container
<Card padding="md">
  <h3>Card Title</h3>
  <p>Card content</p>
</Card>

// FormField with contextual help
<FormField
  label="Holzart"
  tier="tier1"
  helpText='Wood type (e.g., "Eiche", "Buche")'
  icon="💡"
>
  <Input placeholder="Eiche" />
</FormField>
```

### Custom Hooks

```tsx
import { useDocuments, useUploadDocument } from '@/lib/hooks/useDocuments'
import { useProposals, useGenerateProposal } from '@/lib/hooks/useProposals'

// Fetch documents
const { data: documents, isLoading } = useDocuments()

// Upload document
const uploadMutation = useUploadDocument()
await uploadMutation.mutateAsync(file)

// Generate proposal
const proposalMutation = useGenerateProposal()
await proposalMutation.mutateAsync({
  document_id: 'doc-123',
  customer_name: 'John Doe',
  customer_email: 'john@example.com',
})
```

### German Formatters

```tsx
import {
  formatGermanNumber,
  formatGermanCurrency,
  formatGermanDate,
} from '@/lib/utils/formatters'

formatGermanNumber(1234.56, 2)        // "1.234,56"
formatGermanCurrency(2450.80)         // "2.450,80 €"
formatGermanDate(new Date())          // "02.12.2025"
```

## 🧪 Testing

### Unit Tests (Vitest)

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Generate coverage report
npm run test -- --coverage
```

### E2E Tests (Playwright)

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npm run test:e2e

# Run E2E tests in UI mode
npm run test:e2e -- --ui
```

## 🚢 Deployment

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build locally
npm run preview
```

### Environment Variables

Create `.env.production` file:

```bash
VITE_API_URL=https://your-backend-api.run.app
```

### Docker Deployment

```bash
# Build Docker image
docker build -t draftcraft-frontend .

# Run container
docker run -p 80:80 draftcraft-frontend
```

### Google Cloud Run

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT_ID/draftcraft-frontend
gcloud run deploy draftcraft-frontend \
  --image gcr.io/PROJECT_ID/draftcraft-frontend \
  --platform managed \
  --region europe-west3
```

## 📖 Documentation

- **Phase 4B Strategy**: See `/docs/phases/PHASE4B_UI_DEVELOPMENT_STRATEGY.md`
- **Backend API Guide**: See `FRONTEND_INTEGRATION_GUIDE.md`
- **Django Admin Tooltips**: See `backend/ADMIN_TOOLTIPS_GUIDE.md`

## 🎯 Roadmap

### Phase 4B.1: Core UI Setup ✅ COMPLETED
- [x] React + Vite + TypeScript project
- [x] Tailwind CSS configuration
- [x] API client with authentication
- [x] German formatters and utilities
- [x] Base UI components

### Phase 4B.2: Document Workflow ✅ COMPLETED
- [x] Upload component with drag-and-drop
- [x] Processing status display
- [x] Extraction results viewer
- [x] Step-by-step workflow UI

### Phase 4B.3: Proposal Generation ✅ COMPLETED
- [x] Customer form with validation
- [x] Auto-fill from extraction data
- [x] PDF download functionality
- [x] Email sending interface

### Phase 4B.4: Admin Dashboard (PLANNED)
- [ ] Pattern review interface
- [ ] Fix approval workflow
- [ ] Deployment management UI
- [ ] Analytics charts (Recharts)
- [ ] Betriebskennzahlen visualization

### Phase 4B.5: Testing & Polish (PLANNED)
- [ ] Unit tests for utilities (80% coverage)
- [ ] E2E tests for critical workflows
- [ ] Performance optimization (<500KB bundle)
- [ ] Accessibility audit (Lighthouse ≥90)
- [ ] German i18n review

## 🤝 Contributing

### Code Style

- Use TypeScript strict mode
- Follow ESLint rules
- Format with Prettier
- Write descriptive commit messages

### Component Guidelines

1. **Naming**: Use PascalCase for components
2. **Props**: Define TypeScript interfaces
3. **Documentation**: Add JSDoc comments
4. **Accessibility**: Use semantic HTML and ARIA labels
5. **Testing**: Write tests for complex logic

## 📄 License

Copyright © 2025 DraftCraft. All rights reserved.

---

**Status**: ✅ Phase 4B.1-4B.3 Complete | Ready for Development
**Last Updated**: 2025-12-02

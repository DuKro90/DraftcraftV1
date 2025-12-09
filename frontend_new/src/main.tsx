import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

// Configure React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
})

// Development: React Query Devtools (optional - install @tanstack/react-query-devtools to enable)
// if (import.meta.env.DEV) {
//   import('@tanstack/react-query-devtools').then(({ ReactQueryDevtools }) => {
//     queryClient.setDefaultOptions({
//       queries: {
//         ...queryClient.getDefaultOptions().queries,
//       },
//     })
//   })
// }

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)

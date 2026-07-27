import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Toaster } from 'react-hot-toast'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Toaster
      position="top-right"
      toastOptions={{
        duration: 4000,
        style: {
          background: '#1B3A52',
          color: '#FFF8F0',
          border: '2px solid #D4A574',
          fontFamily: 'Commissioner, sans-serif',
          boxShadow: '0 4px 16px rgba(27, 58, 82, 0.2)',
        },
        success: {
          iconTheme: {
            primary: '#D4A574',
            secondary: '#FFF8F0',
          },
        },
        error: {
          iconTheme: {
            primary: '#C94D3C',
            secondary: '#FFF8F0',
          },
        },
      }}
    />
  </StrictMode>,
)

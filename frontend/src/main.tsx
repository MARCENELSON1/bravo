import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import '@/i18n'
import App from './App.tsx'
import { Providers } from '@/app/providers'

// Preferencia local "reducir movimiento": aplicar la clase al arrancar.
if (localStorage.getItem('wellnod:reduce-motion') === '1') {
  document.documentElement.classList.add('reduce-motion')
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <App />
    </Providers>
  </StrictMode>,
)

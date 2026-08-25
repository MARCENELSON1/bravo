import '@testing-library/jest-dom/vitest'
import i18n from '@/i18n' // inicializa i18n para que t() rinda en los tests

// jsdom reporta navigator.language = en-US → forzamos español para que los tests
// (que asertan textos en español) sean deterministas. El test del switcher togglea
// explícitamente. La detección por navegador se prueba aparte en i18n.test.ts.
void i18n.changeLanguage('es')

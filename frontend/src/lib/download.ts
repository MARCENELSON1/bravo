// Dispara la descarga de un Blob en el navegador (crea un object URL temporal,
// hace click en un <a download> y lo limpia). El nombre cae al provisto si el
// servidor no mandó Content-Disposition.
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  // Revocar en el próximo tick para no cancelar la descarga en curso.
  setTimeout(() => URL.revokeObjectURL(url), 0)
}

// Minimal ambient typing for the experimental BarcodeDetector API (used as a
// progressive enhancement for camera QR scanning; the typed-code path is the
// universal fallback).
interface DetectedBarcode {
  rawValue: string
}

interface BarcodeDetectorOptions {
  formats?: string[]
}

declare class BarcodeDetector {
  constructor(options?: BarcodeDetectorOptions)
  detect(source: CanvasImageSource): Promise<DetectedBarcode[]>
  static getSupportedFormats(): Promise<string[]>
}

interface Window {
  BarcodeDetector?: typeof BarcodeDetector
}

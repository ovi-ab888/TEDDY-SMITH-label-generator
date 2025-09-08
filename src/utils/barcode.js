import JsBarcode from 'jsbarcode';

export function generateBarcode(canvas, barcodeText) {
  try {
    JsBarcode(canvas, barcodeText, {
      format: "EAN13",
      displayValue: true,
      fontSize: 14,
      background: "#ffffff",
      lineColor: "#000000"
    });
    return canvas.toDataURL('image/png');
  } catch (error) {
    console.error("Barcode generation error:", error);
    return null;
  }
}

// barcode.js
// 🔹 Local barcode generator for EAN-13 PNG files

async function generateBarcodesFromList(barcodes) {
  const JsBarcodeScript = document.createElement("script");
  JsBarcodeScript.src = "https://cdn.jsdelivr.net/npm/jsbarcode@3.11.6/dist/JsBarcode.all.min.js";
  document.head.appendChild(JsBarcodeScript);

  JsBarcodeScript.onload = async () => {
    const fs = window.fs || require("fs"); // For Node/Electron context
    const dir = "barcode_pngs";
    if (!fs.existsSync(dir)) fs.mkdirSync(dir);

    barcodes.forEach((code) => {
      const canvas = document.createElement("canvas");
      JsBarcode(canvas, code, {
        format: "EAN13",
        lineColor: "#000",
        background: "transparent",
        displayValue: false,
        width: 2,
        height: 90
      });

      const dataURL = canvas.toDataURL("image/png");
      const base64Data = dataURL.replace(/^data:image\/png;base64,/, "");
      fs.writeFileSync(`${dir}/${code}.png`, base64Data, "base64");
      console.log(`✅ Saved: ${code}.png`);
    });
  };
}

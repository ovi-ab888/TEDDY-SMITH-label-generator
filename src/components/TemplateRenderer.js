import { generateBarcode } from '../utils/barcode.js';

export class TemplateRenderer {
  constructor() {
    this.canvas = document.createElement('canvas');
  }

  async renderItem(data) {
    const barcodeDataURL = await generateBarcode(this.canvas, data.barcode);
    
    return `
      <div class="barcode-item">
        <div class="barcode-header">
          <div class="style-name">${data.styleName}</div>
          <div class="color-ref">${data.colorRef}</div>
        </div>
        <div class="barcode-content">
          <div class="art-season">${data.artSeason} ${data.styleRef}</div>
          <div class="size">TAILLE: ${data.size}</div>
          <img src="${barcodeDataURL}" alt="Barcode" class="barcode-image">
          <div class="price">${data.price}</div>
          <div class="consielle">CONSEILLE:</div>
          <div class="prix-vente">PRIX DE VENTE DETAIL</div>
        </div>
      </div>
    `;
  }

  async renderPage(items) {
    const itemsHTML = await Promise.all(items.map(item => this.renderItem(item)));
    return `
      <div class="page">
        ${itemsHTML.join('')}
      </div>
    `;
  }
}

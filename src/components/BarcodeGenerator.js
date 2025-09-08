import { TemplateRenderer } from './TemplateRenderer.js';
import { PDFGenerator } from './PDFGenerator.js';
import { chunkArray } from '../utils/helpers.js';

export class BarcodeGenerator {
  constructor() {
    this.templateRenderer = new TemplateRenderer();
    this.pdfGenerator = new PDFGenerator();
    this.itemsPerPage = 5;
  }

  async generateFromData(data) {
    const chunks = chunkArray(data, this.itemsPerPage);
    const pages = [];
    
    for (const chunk of chunks) {
      const pageHTML = await this.templateRenderer.renderPage(chunk);
      pages.push(pageHTML);
    }

    await this.pdfGenerator.generatePDF(pages);
  }

  async processFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result);
          resolve(data);
        } catch (error) {
          reject(new Error('Invalid JSON file'));
        }
      };
      
      reader.onerror = () => reject(new Error('Error reading file'));
      reader.readAsText(file);
    });
  }
}

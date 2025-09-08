import jsPDF from 'jspdf';
import { chunkArray } from '../utils/helpers.js';

export class PDFGenerator {
  constructor() {
    this.doc = new jsPDF();
    this.currentY = 20;
  }

  addPage() {
    this.doc.addPage();
    this.currentY = 20;
  }

  async generatePDF(pages, filename = 'barcodes.pdf') {
    for (let i = 0; i < pages.length; i++) {
      if (i > 0) this.addPage();
      
      const pageHTML = pages[i];
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = pageHTML;
      
      // SVG টেমপ্লেট যোগ করা হবে এখানে
      // বর্তমানে আমরা HTML content add করতে পারছি
      this.doc.text(`Page ${i + 1}`, 20, this.currentY);
      this.currentY += 10;
    }

    this.doc.save(filename);
  }
}

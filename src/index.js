import { BarcodeGenerator } from './components/BarcodeGenerator.js';
import './styles/main.css';

document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('fileInput');
  const generateBtn = document.getElementById('generateBtn');
  const preview = document.getElementById('preview');
  
  const barcodeGenerator = new BarcodeGenerator();

  generateBtn.addEventListener('click', async () => {
    if (!fileInput.files.length) {
      alert('Please select a JSON file');
      return;
    }

    try {
      const data = await barcodeGenerator.processFile(fileInput.files[0]);
      await barcodeGenerator.generateFromData(data);
      alert('PDF generated successfully!');
    } catch (error) {
      alert('Error: ' + error.message);
    }
  });

  fileInput.addEventListener('change', async (event) => {
    if (event.target.files.length) {
      try {
        const data = await barcodeGenerator.processFile(event.target.files[0]);
        preview.innerHTML = `<p>Loaded ${data.length} items</p>`;
      } catch (error) {
        preview.innerHTML = `<p style="color: red;">${error.message}</p>`;
      }
    }
  });
});

export function formatPrice(price) {
  return price.replace(/,/g, '.');
}

export function validateEAN13(barcode) {
  if (!barcode || barcode.length !== 13) return false;
  
  const digits = barcode.split('').map(Number);
  let sum = 0;
  
  for (let i = 0; i < 12; i++) {
    sum += digits[i] * (i % 2 === 0 ? 1 : 3);
  }
  
  const checksum = (10 - (sum % 10)) % 10;
  return digits[12] === checksum;
}

export function chunkArray(array, size) {
  const result = [];
  for (let i = 0; i < array.length; i += size) {
    result.push(array.slice(i, i + size));
  }
  return result;
}

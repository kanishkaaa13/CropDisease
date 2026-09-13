/**
 * Blur detection utility using Laplacian variance.
 * Detects if an image is too blurry by calculating the variance of the Laplacian.
 * Lower variance indicates blurrier images.
 */

const BLUR_THRESHOLD = 100; // Threshold below which image is considered too blurry

export async function detectBlur(imageFile: File): Promise<{ isBlurry: boolean; variance: number }> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(imageFile);

    img.onload = () => {
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        if (!ctx) {
          reject(new Error('Failed to get canvas context'));
          return;
        }

        // Resize to reasonable size for performance
        const maxSize = 500;
        let width = img.width;
        let height = img.height;

        if (width > height) {
          if (width > maxSize) {
            height *= maxSize / width;
            width = maxSize;
          }
        } else {
          if (height > maxSize) {
            width *= maxSize / height;
            height = maxSize;
          }
        }

        canvas.width = width;
        canvas.height = height;
        ctx.drawImage(img, 0, 0, width, height);

        const imageData = ctx.getImageData(0, 0, width, height);
        const variance = calculateLaplacianVariance(imageData.data, width, height);

        URL.revokeObjectURL(url);

        resolve({
          isBlurry: variance < BLUR_THRESHOLD,
          variance
        });
      } catch (error) {
        URL.revokeObjectURL(url);
        reject(error);
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error('Failed to load image'));
    };

    img.src = url;
  });
}

function calculateLaplacianVariance(data: Uint8ClampedArray, width: number, height: number): number {
  // Convert to grayscale and apply Laplacian kernel
  const grayscale = new Float32Array(width * height);
  
  for (let i = 0; i < data.length; i += 4) {
    const idx = i / 4;
    grayscale[idx] = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
  }

  // Apply Laplacian kernel: [[0, -1, 0], [-1, 4, -1], [0, -1, 0]]
  const laplacian = new Float32Array(width * height);
  
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const center = grayscale[idx];
      const top = grayscale[idx - width];
      const bottom = grayscale[idx + width];
      const left = grayscale[idx - 1];
      const right = grayscale[idx + 1];
      
      laplacian[idx] = 4 * center - top - bottom - left - right;
    }
  }

  // Calculate variance
  let sum = 0;
  let sumSquared = 0;
  const count = (width - 2) * (height - 2);

  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = y * width + x;
      const val = laplacian[idx];
      sum += val;
      sumSquared += val * val;
    }
  }

  const mean = sum / count;
  const variance = (sumSquared / count) - (mean * mean);

  return variance;
}

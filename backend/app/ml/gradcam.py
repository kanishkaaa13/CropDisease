"""
Grad-CAM (Gradient-weighted Class Activation Mapping) Generator.
Produces visual explanations for EfficientNet-B0 predictions by overlaying
gradient heatmaps on target crop leaf images.
"""
import base64
import io
from typing import Tuple, Optional

import numpy as np

try:
    import cv2
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _HAS_TORCH = True
except ImportError:
    _HAS_TORCH = False
    cv2 = None
    torch = None
    nn = None
    F = None
from PIL import Image


class GradCAM:
    """
    Grad-CAM explanation generator targeting the final convolutional layer of EfficientNet-B0.
    """

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None):
        self.model = model
        self.model.eval()

        # Default target layer for EfficientNet-B0 is features[-1]
        if target_layer is None:
            if hasattr(self.model, "features"):
                self.target_layer = self.model.features[-1]
            else:
                # Fallback to last conv module found
                self.target_layer = [m for m in self.model.modules() if isinstance(m, nn.Conv2d)][-1]
        else:
            self.target_layer = target_layer

        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None

        # Register forward & backward hooks
        self._register_hooks()

    def _register_hooks(self):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_in, grad_out):
            self.gradients = grad_out[0].detach()

        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class_idx: int
    ) -> np.ndarray:
        """
        Generate raw Grad-CAM heatmap array normalized in range [0, 1].
        """
        self.model.zero_grad()

        # Forward pass
        output = self.model(input_tensor)

        if target_class_idx is None:
            target_class_idx = output.argmax(dim=1).item()

        # Target class score
        score = output[0, target_class_idx]
        score.backward(retain_graph=True)

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations were not captured by hooks.")

        # Global average pooling of gradients: alpha_k = (1/Z) * sum_{i,j} (d y_c / d A_{i,j}^k)
        gradients = self.gradients[0]  # (C, H, W)
        activations = self.activations[0]  # (C, H, W)

        weights = torch.mean(gradients, dim=(1, 2), keepdim=True)  # (C, 1, 1)

        # Weighted combination of feature maps
        cam = torch.sum(weights * activations, dim=0)  # (H, W)

        # Apply ReLU to keep positive contribution pixels
        cam = F.relu(cam)

        cam_np = cam.cpu().numpy()

        # Normalize [0, 1]
        if cam_np.max() > 0:
            cam_np = cam_np / cam_np.max()

        return cam_np

    def overlay_heatmap_on_image(
        self,
        pil_image: Image.Image,
        heatmap_np: np.ndarray,
        alpha: float = 0.5,
        colormap: int = cv2.COLORMAP_JET
    ) -> Tuple[Image.Image, str]:
        """
        Overlay Grad-CAM heatmap onto the original PIL image.
        Returns:
            - PIL Image with heatmap overlay
            - Base64 encoded PNG string ("data:image/png;base64,...")
        """
        # Convert PIL to BGR OpenCV image
        orig_img_np = np.array(pil_image.convert("RGB"))
        h, w, _ = orig_img_np.shape

        # Resize heatmap to original image dimensions
        heatmap_resized = cv2.resize(heatmap_np, (w, h))

        # Convert heatmap to 8-bit unsigned int
        heatmap_uint8 = np.uint8(255 * heatmap_resized)

        # Apply OpenCV COLORMAP_JET
        color_heatmap = cv2.applyColorMap(heatmap_uint8, colormap)
        color_heatmap_rgb = cv2.cvtColor(color_heatmap, cv2.COLOR_BGR2RGB)

        # Blend original image and heatmap
        blended = cv2.addWeighted(orig_img_np, 1.0 - alpha, color_heatmap_rgb, alpha, 0)
        blended_pil = Image.fromarray(blended)

        # Convert to Base64 PNG string
        buffered = io.BytesIO()
        blended_pil.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_uri = f"data:image/png;base64,{img_str}"

        return blended_pil, base64_uri

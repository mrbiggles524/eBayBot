"""Image watermarking - add optional watermark to card images."""
import io
import os
from typing import Optional

# Pillow is optional - degrade gracefully if not installed
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


class ImageWatermarker:
    """Add text watermark to images."""
    
    def __init__(
        self,
        text: str = "CardLister Pro",
        opacity: float = 0.3,
        font_size: int = 24
    ):
        self.text = text
        self.opacity = max(0.1, min(1.0, opacity))
        self.font_size = font_size
    
    def add_watermark_to_url(
        self,
        image_url: str,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Fetch image from URL, add watermark, return bytes or save to output_path.
        Returns None if Pillow not installed or image fetch fails.
        """
        if not HAS_PILLOW:
            return None
        try:
            import requests
            r = requests.get(image_url, timeout=15)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content)).convert('RGBA')
            watermarked = self._apply_watermark(img)
            out = io.BytesIO()
            watermarked.convert('RGB').save(out, format='JPEG', quality=90)
            data = out.getvalue()
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(data)
            return data
        except Exception:
            return None
    
    def _apply_watermark(self, img: 'Image.Image') -> 'Image.Image':
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        try:
            font = ImageFont.truetype("arial.ttf", self.font_size)
        except Exception:
            font = ImageFont.load_default()
        
        # Bottom-right, semi-transparent
        bbox = draw.textbbox((0, 0), self.text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = img.size[0] - tw - 20, img.size[1] - th - 20
        draw.text((x, y), self.text, font=font, fill=(255, 255, 255, int(255 * self.opacity)))
        
        return Image.alpha_composite(img, overlay)

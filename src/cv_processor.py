"""
Computer Vision Processor for Mechanical Drawings
Handles all OpenCV and image processing operations
"""

from typing import Dict, List
import cv2
import numpy as np
from PIL import Image
import io
import base64


class CVProcessor:
    """
    Computer Vision processor for mechanical drawings.
    
    Think of this as the "eyes" of the system:
    - Detects regions (title blocks, views, tables)
    - Enhances text for better OCR
    - Prepares images for LLM consumption
    """
    
    def __init__(self, 
                 min_region_area: int = 5000,
                 edge_threshold: tuple = (50, 150)):
        """
        Initialize CV processor with configuration.
        
        Like setting up a camera with specific settings:
        - min_region_area: Minimum size to consider a region important
        - edge_threshold: Sensitivity for edge detection
        """
        self.min_region_area = min_region_area
        self.edge_threshold = edge_threshold
    
    def process_drawing(self, image_path: str) -> Dict:
        """
        Main processing method - what the orchestrator calls.
        
        Args:
            image_path: Path to the mechanical drawing image
            
        Returns:
            Dictionary with processed images and metadata
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Detect regions
        regions = self._detect_regions(enhanced)
        
        # Enhance text areas
        text_regions = self._enhance_text_regions(enhanced)
        
        # Prepare all images for LLM
        processed_images = {
            'full': self._prepare_for_llm(img),
            'enhanced': self._prepare_for_llm(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)),
            'regions': []
        }
        
        # Process individual regions
        for region in regions:
            x, y, w, h = region['bbox']
            region_img = img[y:y+h, x:x+w]
            processed_images['regions'].append({
                'type': region['type'],
                'bbox': region['bbox'],
                'image': self._prepare_for_llm(region_img)
            })
        
        # Return in the format the orchestrator expects
        return {
            'processed_images': processed_images,
            'regions': regions,
            'metadata': {
                'total_regions': len(regions),
                'image_shape': img.shape,
                'region_types': list(set(r['type'] for r in regions))
            }
        }
    
    def _detect_regions(self, gray: np.ndarray) -> List[Dict]:
        """Detect major regions in the drawing"""
        regions = []
        
        edges = cv2.Canny(gray, *self.edge_threshold)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_h, img_w = gray.shape
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_region_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            region_type = self._classify_region(x, y, w, h, img_w, img_h)
            
            regions.append({
                'type': region_type,
                'bbox': (x, y, w, h),
                'area': area
            })
        
        return regions
    
    def _classify_region(self, x: int, y: int, w: int, h: int, 
                        img_w: int, img_h: int) -> str:
        """Classify a region based on its position and size"""
        # Title block is usually bottom-right
        if x > img_w * 0.6 and y > img_h * 0.7:
            return 'title_block'
        # Tables often have specific aspect ratios
        elif 0.3 < w/h < 3 and w > img_w * 0.2:
            return 'table'
        # Main views take up significant space
        elif w > img_w * 0.25 or h > img_h * 0.25:
            return 'drawing_view'
        else:
            return 'detail'
    
    def _enhance_text_regions(self, gray: np.ndarray) -> np.ndarray:
        """Enhance text regions for better recognition"""
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        _, text_mask = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return text_mask
    
    def _prepare_for_llm(self, img: np.ndarray) -> str:
        """Convert image to base64 for LLM input"""
        if len(img.shape) == 2:
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
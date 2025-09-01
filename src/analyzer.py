"""
Mechanical Drawing Analyzer with Computer Vision and LLM
Co-Author: AI-assisted development with Claude (Anthropic)
"""

import cv2
import numpy as np
import base64
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field
import json
from openai import OpenAI  # or use local models via Ollama/LlamaCpp
from PIL import Image
import io
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in parent directory if running from src/
env_path = Path(__file__).parent.parent / '.env'
if not env_path.exists():
    env_path = Path('.env')  # Fallback to current directory

load_dotenv(env_path, override=True)
openai_api_key = os.getenv("OPENAI_API_KEY")
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

# Only print API key status in debug mode or when running directly
if __name__ == "__main__":
    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")
        
    if anthropic_api_key:
        print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("Anthropic API Key not set")

# Pydantic models for structured output (function calling)
class Dimension(BaseModel):
    """Structured dimension extraction"""
    value: float = Field(description="Numerical value of the dimension")
    unit: str = Field(description="Unit (mm, in, cm)")
    tolerance_upper: Optional[float] = Field(None, description="Upper tolerance if specified")
    tolerance_lower: Optional[float] = Field(None, description="Lower tolerance if specified")
    feature: str = Field(description="What this dimension measures (e.g., 'hole diameter', 'overall length')")
    confidence: float = Field(description="Confidence score 0-1")

class GDTSymbol(BaseModel):
    """GD&T symbol information"""
    symbol_type: str = Field(description="Type: flatness, perpendicularity, position, etc.")
    tolerance: float = Field(description="Tolerance value")
    datum_references: List[str] = Field(default_factory=list, description="Referenced datums")
    applies_to: str = Field(description="Feature this applies to")

class DrawingView(BaseModel):
    """Information about a specific view"""
    view_type: str = Field(description="top, front, side, section, detail, isometric")
    scale: Optional[str] = Field(None, description="Scale if specified (e.g., '1:2')")
    contains_features: List[str] = Field(description="List of visible features")
    
class PartSpecification(BaseModel):
    """Complete part specification from drawing"""
    part_number: Optional[str] = None
    material: Optional[str] = None
    overall_dimensions: Dict[str, Dimension] = Field(default_factory=dict)  # length, width, height
    critical_dimensions: List[Dimension] = Field(default_factory=list)
    gdt_requirements: List[GDTSymbol] = Field(default_factory=list)
    views: List[DrawingView] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    title_block_info: Dict[str, str] = Field(default_factory=dict)

class MechanicalDrawingAnalyzer:
    """Hybrid CV + LLM analyzer for mechanical drawings"""
    
    def __init__(self, llm_provider="openai", model=None, 
                 local_model=None):
        self.llm_provider = llm_provider
        
        # Set default models based on provider
        if model is None:
            if llm_provider == "openai":
                model = "gpt-4.1-mini"  # or gpt-4o-mini for cheaper
            elif llm_provider == "claude":
                model = "claude-3-5-haiku-latest"  # or claude-opus-4-1-20250805 || claude-sonnet-4-20250514
            elif llm_provider == "ollama":
                model = local_model or "gemma3:4b"  # or "llava:13b" || "bakllava" || other compatible models
                
        self.model = model
        
        # Initialize LLM client
        if llm_provider == "openai":
            self.client = OpenAI()  # Expects OPENAI_API_KEY env var
        elif llm_provider == "ollama":
            # For local models like LLaVA or BakLLaVA
            import ollama
            self.client = ollama
        elif llm_provider == "claude":
            # For Claude via API
            import anthropic
            self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        
        # CV parameters
        self.min_region_area = 5000
        self.edge_threshold = (50, 150)
        
    def preprocess_drawing(self, image_path: str) -> Dict:
        """Use OpenCV to preprocess and segment the drawing"""
        
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Enhance contrast for better LLM recognition
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        
        # Detect major regions (views, title block, tables)
        regions = self._detect_regions(enhanced)
        
        # Detect and enhance text areas
        text_regions = self._enhance_text_regions(enhanced)
        
        # Prepare images for LLM
        processed_images = {
            'full': self._prepare_for_llm(img),
            'enhanced': self._prepare_for_llm(cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)),
            'regions': []
        }
        
        # Extract individual regions for focused analysis
        for region in regions:
            x, y, w, h = region['bbox']
            region_img = img[y:y+h, x:x+w]
            processed_images['regions'].append({
                'type': region['type'],
                'bbox': region['bbox'],
                'image': self._prepare_for_llm(region_img)
            })
        
        return processed_images
    
    def _detect_regions(self, gray: np.ndarray) -> List[Dict]:
        """Detect major regions in the drawing"""
        regions = []
        
        # Use edge detection and contours
        edges = cv2.Canny(gray, *self.edge_threshold)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_h, img_w = gray.shape
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_region_area:
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            
            # Classify region based on position and aspect ratio
            region_type = self._classify_region(x, y, w, h, img_w, img_h)
            
            regions.append({
                'type': region_type,
                'bbox': (x, y, w, h),
                'contour': contour
            })
        
        return regions
    
    def _classify_region(self, x: int, y: int, w: int, h: int, 
                        img_w: int, img_h: int) -> str:
        """Heuristic classification of regions"""
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
        """Enhance text for better OCR by LLM"""
        # Morphological operations to connect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Threshold for text
        _, text_mask = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return text_mask
    
    def _prepare_for_llm(self, img: np.ndarray) -> str:
        """Convert image to base64 for LLM input"""
        # Convert to PIL Image
        if len(img.shape) == 2:
            pil_img = Image.fromarray(img)
        else:
            pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        # Convert to base64
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def analyze_with_llm(self, processed_images: Dict, 
                        compliance_rules: Optional[List[str]] = None) -> PartSpecification:
        """Use LLM to understand the drawing content"""
        
        # Build the prompt
        prompt = self._build_analysis_prompt(compliance_rules)
        
        if self.llm_provider == "openai":
            return self._analyze_with_gpt4v(processed_images, prompt)
        elif self.llm_provider == "ollama":
            return self._analyze_with_ollama(processed_images, prompt)
        elif self.llm_provider == "claude":
            return self._analyze_with_claude(processed_images, prompt)
    
    def _build_analysis_prompt(self, compliance_rules: Optional[List[str]]) -> str:
        """Build the analysis prompt"""
        base_prompt = """You are an expert mechanical engineer analyzing technical drawings. 
        Extract the following information from this mechanical drawing:

        1. Part identification (number, name, material)
        2. Overall dimensions (length, width, height) with units and tolerances
        3. Critical dimensions with their tolerances and what they measure
        4. All GD&T symbols with their tolerances and datum references
        5. Different views present (top, front, side, section, etc.)
        6. Any notes or special requirements
        7. Title block information

        Focus on:
        - Precise dimension values including tolerances (±)
        - GD&T symbols (⊥, ∥, ◯, ⌖, etc.) 
        - Datum references (A, B, C)
        - Surface finish requirements
        - Any threaded features or holes
        """
        
        if compliance_rules:
            base_prompt += "\n\nAlso check these compliance rules:\n"
            for rule in compliance_rules:
                base_prompt += f"- {rule}\n"
        
        return base_prompt
    
    def _analyze_with_gpt4v(self, processed_images: Dict, prompt: str) -> PartSpecification:
        """Analyze using GPT-4 Vision with function calling"""
        
        messages = [
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this mechanical drawing. First show the full drawing:"},
                    {"type": "image_url", "image_url": {"url": processed_images['full']}}
                ]
            }
        ]
        
        # Add region images for detailed analysis
        for region in processed_images['regions']:
            if region['type'] == 'title_block':
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Here's the title block in detail:"},
                        {"type": "image_url", "image_url": {"url": region['image']}}
                    ]
                })
        
        # Use function calling for structured output
        tools = [{
            "type": "function",
            "function": {
                "name": "extract_part_specification",
                "description": "Extract structured part specification from drawing",
                "parameters": PartSpecification.model_json_schema()
            }
        }]
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "extract_part_specification"}}
        )
        
        # Parse the function call response
        function_args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        return PartSpecification(**function_args)
    
    def _analyze_with_ollama(self, processed_images: Dict, prompt: str) -> PartSpecification:
        """Analyze using Ollama (local model)"""
        # Implementation for Ollama
        # This is a placeholder - you'd need to implement based on Ollama's API
        raise NotImplementedError("Ollama integration needs to be implemented")
    
    def _analyze_with_claude(self, processed_images: Dict, prompt: str) -> PartSpecification:
        """Analyze using Claude"""
        # Implementation for Claude
        # This is a placeholder - you'd need to implement based on Anthropic's API
        raise NotImplementedError("Claude integration needs to be implemented")
    
    def analyze_drawing(self, image_path: str, 
                       compliance_rules: Optional[List[str]] = None,
                       design_rules: Optional[Dict] = None) -> Dict:
        """Complete analysis pipeline - convenience method"""
        
        # Preprocess
        processed = self.preprocess_drawing(image_path)
        
        # Analyze with LLM
        spec = self.analyze_with_llm(processed, compliance_rules)
        
        # Check compliance if rules provided
        violations = []
        if design_rules:
            violations = self.check_compliance(spec, design_rules)
        
        return {
            'specification': spec,
            'violations': violations,
            'processed_images': processed
        }
    
    def _convert_to_mm(self, value: float, unit: str) -> float:
        """Convert a measurement to millimeters"""
        conversion_factors = {
            'mm': 1.0,
            'cm': 10.0,
            'in': 25.4,
            'ft': 304.8
        }
        unit = unit.lower()
        if unit not in conversion_factors:
            raise ValueError(f"Unsupported unit: {unit}")
        return value * conversion_factors[unit]

    def check_compliance(self, spec: PartSpecification, rules: Dict) -> List[str]:
        """Check extracted specifications against design rules"""
        violations = []
        
        # Example compliance checks
        if 'min_wall_thickness' in rules:
            for dim in spec.critical_dimensions:
                if 'wall' in dim.feature.lower() or 'thickness' in dim.feature.lower():
                    # Convert dimension to mm for comparison
                    value_in_mm = self._convert_to_mm(dim.value, dim.unit)
                    if value_in_mm < rules['min_wall_thickness']:
                        violations.append(
                            f"Wall thickness {dim.value}{dim.unit} ({value_in_mm:.2f}mm) below minimum "
                            f"{rules['min_wall_thickness']}mm"
                        )
        
        if 'max_aspect_ratio' in rules:
            if 'length' in spec.overall_dimensions and 'width' in spec.overall_dimensions:
                length = spec.overall_dimensions['length'].value
                width = spec.overall_dimensions['width'].value
                ratio = length / width if width > 0 else float('inf')
                
                if ratio > rules['max_aspect_ratio']:
                    violations.append(f"Aspect ratio {ratio:.2f} exceeds maximum {rules['max_aspect_ratio']}")
        
        # Check GD&T requirements
        if 'max_position_tolerance' in rules:
            for gdt in spec.gdt_requirements:
                if gdt.symbol_type == 'position' and gdt.tolerance > rules['max_position_tolerance']:
                    violations.append(
                        f"Position tolerance {gdt.tolerance} exceeds maximum "
                        f"{rules['max_position_tolerance']}"
                    )
        
        return violations


# Simplified Usage Example
def main():
    """Main function for testing the analyzer"""
    
    # Determine the path to the example drawing
    # Check if we're running from src/ or from root
    if Path("examples/mechanical_drawing.png").exists():
        drawing_path = "examples/mechanical_drawing.png"
    elif Path("../examples/mechanical_drawing.png").exists():
        drawing_path = "../examples/mechanical_drawing.png"
    else:
        drawing_path = "mechanical_drawing.png"  # Fallback to current directory
    
    # Check if file exists
    if not Path(drawing_path).exists():
        print(f"Error: Could not find drawing at {drawing_path}")
        print("Please ensure mechanical_drawing.png is in the examples/ folder")
        return

    # Initialize analyzer
    analyzer = MechanicalDrawingAnalyzer(
        llm_provider="openai",  # or "ollama" for local
        model="gpt-4o-mini"  # Updated to match your model name
    )
    
    # Process drawing
    print(f"Preprocessing drawing from {drawing_path}...")
    processed = analyzer.preprocess_drawing(drawing_path)
    
    # Define compliance rules
    compliance_rules = [
        "Minimum wall thickness: 2mm",
        "Maximum aspect ratio: 10:1",
        "All holes must have position tolerance ≤0.1mm",
        "Surface roughness must be specified for mating surfaces"
    ]
    
    design_rules = {
        'min_wall_thickness': 2.0,  # mm
        'max_aspect_ratio': 10.0,
        'max_position_tolerance': 0.1  # mm
    }
    
    # Analyze with LLM
    print("Analyzing with LLM...")
    spec = analyzer.analyze_with_llm(processed, compliance_rules)
    
    # Check compliance
    print("\n=== Part Specification ===")
    print(f"Part Number: {spec.part_number}")
    print(f"Material: {spec.material}")
    print(f"Views detected: {[v.view_type for v in spec.views]}")
    print(f"Critical dimensions: {len(spec.critical_dimensions)}")
    print(f"GD&T requirements: {len(spec.gdt_requirements)}")
    
    violations = analyzer.check_compliance(spec, design_rules)
    if violations:
        print("\n⚠️ Compliance Violations:")
        for v in violations:
            print(f"  - {v}")
    else:
        print("\n✅ All compliance checks passed")
    
    # Export results
    output_path = Path("part_analysis.json")
    with open(output_path, "w") as f:
        json.dump(spec.model_dump(), f, indent=2)
    
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
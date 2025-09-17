from pydantic import BaseModel, Field
from typing import List, Dict, Optional

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

class DrawingAnalysisResult(BaseModel):
    file_path: str
    specification: PartSpecification
    compliance_violations: List[str] = Field(default_factory=list)
    cv_metadata: Dict = Field(default_factory=dict)
    rag_context: Optional[List[Dict]] = None
    processing_info: Dict = Field(default_factory=dict)


"""
Mechanical Drawing Analyzer - Main Orchestrator
Refactored for modularity and dependency injection
Co-Author: AI-assisted development with Claude (Anthropic)
"""

import json
from typing import Dict, List, Optional
from pathlib import Path

# Import modular components (running from project root)
from src.cv_processor import CVProcessor
from src.llm_client import LLMClient
from src.models import PartSpecification, DrawingAnalysisResult
from src.config import AnalyzerConfig
from src.compliance_rules import ComplianceChecker


class MechanicalDrawingAnalyzer:
    """
    Main orchestrator for mechanical drawing analysis.
    
    Think of this as the conductor of an orchestra:
    - CVProcessor is the strings section (handles visual processing)
    - LLMClient is the brass section (handles intelligence/interpretation)
    - ComplianceChecker is the percussion (keeps everything in rhythm/rules)
    - This class conducts them all to create the symphony (analysis)
    """
    
    def __init__(self, 
                 config: Optional[AnalyzerConfig] = None,
                 cv_processor: Optional[CVProcessor] = None,
                 llm_client: Optional[LLMClient] = None,
                 compliance_checker: Optional[ComplianceChecker] = None,
                 rag_engine=None):  # Future RAG integration
        """
        Initialize with dependency injection pattern.
        
        Why dependency injection? It's like a smartphone with swappable parts:
        - You can swap the camera module (CV) without changing the phone
        - You can upgrade the processor (LLM) independently
        - You can add new modules (RAG) without breaking existing ones
        
        Args:
            config: Configuration object (if None, uses defaults)
            cv_processor: Computer vision module (if None, creates default)
            llm_client: LLM communication module (if None, creates default)
            compliance_checker: Rules checking module (if None, creates default)
            rag_engine: RAG module for context retrieval (optional, for future)
        """
        # Load configuration
        self.config = config or AnalyzerConfig()
        
        # Initialize components with dependency injection
        # If not provided, create default instances
        self.cv = cv_processor or CVProcessor(
            min_region_area=self.config.cv_config.min_region_area,
            edge_threshold=self.config.cv_config.edge_threshold
        )
        
        self.llm = llm_client or LLMClient(
            provider=self.config.llm_config.provider,
            model=self.config.llm_config.model,
            api_key=self.config.llm_config.api_key
        )
        
        self.compliance = compliance_checker or ComplianceChecker()
        
        # RAG is optional for now - you'll build this!
        self.rag = rag_engine
        
        # Results cache (useful for RAG later)
        self._analysis_cache = {}
    
    def analyze_drawing(self, 
                       image_path: str,
                       use_rag: bool = False,
                       compliance_rules: Optional[Dict] = None,
                       save_intermediate: bool = False) -> DrawingAnalysisResult:
        """
        Main analysis pipeline - orchestrates all components.
        
        This is like a factory assembly line:
        1. CV station: Extract visual features
        2. RAG station (optional): Find similar drawings
        3. LLM station: Interpret and extract specifications
        4. Compliance station: Check against rules
        5. Package and ship: Return results
        
        Args:
            image_path: Path to the mechanical drawing
            use_rag: Whether to use RAG for context (when you build it!)
            compliance_rules: Dict of rules to check against
            save_intermediate: Whether to save intermediate processing results
            
        Returns:
            DrawingAnalysisResult with all extracted information
        """
        # Validate input
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Drawing not found: {image_path}")
        
        # Step 1: Computer Vision Processing
        print(f"🔍 Processing image: {Path(image_path).name}")
        cv_results = self.cv.process_drawing(image_path)
        
        if save_intermediate:
            self._save_intermediate_results(image_path, "cv", cv_results)
        
        # Step 2: RAG Context Retrieval (if enabled and available)
        rag_context = None
        if use_rag and self.rag:
            print("📚 Retrieving similar drawings context...")
            try:
                rag_context = self.rag.retrieve_context(
                    image_features=cv_results.get('features'),
                    query_embedding=cv_results.get('embedding')
                )
                print(f"  Found {len(rag_context)} relevant references")
            except Exception as e:
                print(f"  ⚠️ RAG retrieval failed: {e}")
                # Continue without RAG context
        
        # Step 3: LLM Analysis
        print("🤖 Analyzing with LLM...")
        analysis_prompt = self._build_analysis_prompt(cv_results, rag_context, compliance_rules)
        
        specification = self.llm.analyze(
            images=cv_results['processed_images'],
            prompt=analysis_prompt,
            structured_output=PartSpecification
        )
        
        # Step 4: Compliance Checking
        violations = []
        if compliance_rules:
            print("✅ Checking compliance...")
            violations = self.compliance.check_specification(
                specification.model_dump(),
                compliance_rules
            )
            print(f"  Found {len(violations)} violations")
        
        # Step 5: Package Results
        result = DrawingAnalysisResult(
            file_path=image_path,
            specification=specification,
            compliance_violations=violations,
            cv_metadata=cv_results.get('metadata', {}),
            rag_context=rag_context,
            processing_info={
                'cv_regions_found': len(cv_results.get('regions', [])),
                'rag_enabled': use_rag and self.rag is not None,
                'rag_contexts_used': len(rag_context) if rag_context else 0,
                'llm_provider': self.config.llm_config.provider,
                'llm_model': self.config.llm_config.model
            }
        )
        
        # Cache for potential RAG use later
        self._analysis_cache[image_path] = result
        
        return result
    
    def _build_analysis_prompt(self, 
                              cv_results: Dict,
                              rag_context: Optional[List[Dict]],
                              compliance_rules: Optional[Dict]) -> str:
        """
        Build the analysis prompt for the LLM.
        
        Like writing a detailed work order for a specialist:
        - What to look for (base instructions)
        - Reference examples (RAG context)
        - Special requirements (compliance rules)
        """
        base_prompt = """You are an expert mechanical engineer analyzing technical drawings. 
        Extract the following information from this mechanical drawing:

        1. Part identification (number, name, material)
        2. Overall dimensions (length, width, height) with units and tolerances
        3. Critical dimensions with their tolerances and what they measure
        4. All GD&T symbols with their tolerances and datum references
        5. Different views present (top, front, side, section, etc.)
        6. Any notes or special requirements
        7. Title block information

        Focus on precision and completeness."""
        
        # Add RAG context if available
        if rag_context:
            base_prompt += "\n\n## Reference Context from Similar Drawings:\n"
            for idx, context in enumerate(rag_context[:3], 1):  # Limit to top 3
                base_prompt += f"\n### Reference {idx}:\n"
                # Domain knowledge context
                base_prompt += f"- Standard: {context.get('title', 'Unknown')}\n"
                base_prompt += f"- Relevance: {context.get('content', 'Unknown')}\n"
                base_prompt += f"- Key specs: {context.get('summary', 'N/A')}\n"
        
        # Add compliance rules if provided
        if compliance_rules:
            base_prompt += "\n\n## Compliance Requirements to Check:\n"
            if 'text_rules' in compliance_rules:
                for rule in compliance_rules['text_rules']:
                    base_prompt += f"- {rule}\n"
        
        # Add CV-detected regions info
        if 'regions' in cv_results:
            base_prompt += f"\n\n## Detected Regions:\n"
            region_types = [r['type'] for r in cv_results['regions']]
            base_prompt += f"Found {len(region_types)} regions: {', '.join(set(region_types))}\n"
        
        return base_prompt
    
    def _save_intermediate_results(self, image_path: str, stage: str, data: Dict):
        """Save intermediate processing results for debugging/analysis."""
        output_dir = Path("intermediate_results")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{Path(image_path).stem}_{stage}.json"
        output_path = output_dir / filename
        
        # Remove non-serializable data (like images)
        clean_data = {k: v for k, v in data.items() 
                     if not k.endswith('_image') and k != 'processed_images'}
        
        with open(output_path, 'w') as f:
            json.dump(clean_data, f, indent=2, default=str)
        
        print(f"  💾 Saved {stage} results to {output_path}")
    
    def update_component(self, component_name: str, new_component):
        """
        Hot-swap a component at runtime.
        
        Like changing a tire while the car is parked:
        - Safe to do
        - Doesn't affect other components
        - Can test different implementations easily
        
        Args:
            component_name: 'cv', 'llm', 'compliance', or 'rag'
            new_component: The new component instance
        """
        valid_components = ['cv', 'llm', 'compliance', 'rag']
        if component_name not in valid_components:
            raise ValueError(f"Component must be one of {valid_components}")
        
        setattr(self, component_name, new_component)
        print(f"✨ Updated {component_name} component")
    
    def get_analysis_summary(self, result: DrawingAnalysisResult) -> str:
        """
        Generate a human-readable summary of the analysis.
        
        Like an executive summary of a report:
        - Key findings
        - Important metrics
        - Action items (violations)
        """
        spec = result.specification
        summary = f"""
            📋 Drawing Analysis Summary
            {'='*50}
            📁 File: {Path(result.file_path).name}
            🏷️ Part Number: {spec.part_number or 'Not specified'}
            🔧 Material: {spec.material or 'Not specified'}

            📐 Dimensions:
            - Critical dimensions found: {len(spec.critical_dimensions)}
            - Views identified: {', '.join([v.view_type for v in spec.views])}
            - GD&T requirements: {len(spec.gdt_requirements)}

            """
        if result.compliance_violations:
            summary += f"""⚠️ Compliance Issues: {len(result.compliance_violations)}"""
            for v in result.compliance_violations[:3]:  # Show first 3
                summary += f"  - {v}\n"
            if len(result.compliance_violations) > 3:
                summary += f"  ... and {len(result.compliance_violations) - 3} more\n"
        else:
            summary += "✅ All compliance checks passed\n"
        
        if result.rag_context:
            summary += f"\n📚 Referenced {len(result.rag_context)} similar drawings\n"
        
        return summary


# Simplified usage example
def main():
    """Example usage of the refactored analyzer."""
    from pathlib import Path
    
    # Create analyzer with default components
    analyzer = MechanicalDrawingAnalyzer()
    
    # Or create with custom configuration
    # config = AnalyzerConfig(
    #     llm_config={'provider': 'ollama', 'model': 'llava'}
    # )
    # analyzer = MechanicalDrawingAnalyzer(config=config)
    
    # Find example drawing
    drawing_paths = [
        "examples/mechanical_drawing.png",
        "../examples/mechanical_drawing.png",
        "mechanical_drawing.png"
    ]
    
    drawing_path = None
    for path in drawing_paths:
        if Path(path).exists():
            drawing_path = path
            break
    
    if not drawing_path:
        print("❌ Could not find example drawing")
        return
    
    # Define compliance rules
    compliance_rules = {
        'text_rules': [
            "Minimum wall thickness: 2mm",
            "Maximum aspect ratio: 10:1"
        ],
        'numeric_rules': {
            'min_wall_thickness': 2.0,
            'max_aspect_ratio': 10.0
        }
    }
    
    # Analyze drawing
    print(f"\n🔧 Analyzing: {drawing_path}\n")
    result = analyzer.analyze_drawing(
        image_path=drawing_path,
        use_rag=False,  # Will be True when you build RAG!
        compliance_rules=compliance_rules,
        save_intermediate=True
    )
    
    # Print summary
    print(analyzer.get_analysis_summary(result))
    
    # Save detailed results
    output_file = Path("analysis_result.json")
    with open(output_file, 'w') as f:
        json.dump(result.model_dump(), f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to {output_file}")


if __name__ == "__main__":
    main()
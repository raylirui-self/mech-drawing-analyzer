"""Test the complete orchestrator system"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.mech_dwg_orchestrator import MechanicalDrawingAnalyzer

def test_orchestrator():
    print("Testing Orchestrator System\n" + "="*50)
    
    # Create analyzer
    try:
        analyzer = MechanicalDrawingAnalyzer()
        print("✅ Orchestrator initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return False
    
    # Find test image
    test_paths = [
        "examples/mechanical_drawing.png",
        "mechanical_drawing.png"
    ]
    
    image_path = None
    for path in test_paths:
        if Path(path).exists():
            image_path = path
            break
    
    if not image_path:
        print("❌ No test image found")
        return False
    
    # Test analysis
    try:
        result = analyzer.analyze_drawing(
            image_path=image_path,
            use_rag=False,  # RAG not built yet
            save_intermediate=True
        )
        print("✅ Analysis completed!")
        print(analyzer.get_analysis_summary(result))
        return True
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_orchestrator()
    if success:
        print("\n🎉 System ready for RAG integration!")
    else:
        print("\n⚠️ Fix issues before proceeding to RAG")
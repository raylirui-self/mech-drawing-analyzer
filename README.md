# Mechanical Drawing Analyzer

An AI-powered system for analyzing mechanical engineering drawings, extracting dimensions, GD&T symbols, and checking compliance with design rules.

## 🌟 Features

- **Automated Drawing Analysis**: Extract dimensions, tolerances, and GD&T symbols from technical drawings
- **Multi-Model Support**: Works with GPT, Claude, and local models (Gemma3 via Ollama)
- **Compliance Checking**: Validate drawings against customizable design rules
- **Smart Preprocessing**: Enhanced image processing using OpenCV for better recognition
- **Structured Output**: Pydantic models for reliable data extraction
- **Custom Rules**: Define and validate your own engineering design rules
- **Fine-tuning Support**: Tools to fine-tune vision models on your own drawings

## 🚀 Quick Start

### Prerequisites

- 16GB RAM recommended
- GPU with 8GB+ VRAM (optional, for local models)

### Supported Models

The analyzer supports multiple vision-language models:

1. **OpenAI GPT-4.1-mini** (Default)
   - Requires OpenAI API key
   - Set in .env: `OPENAI_API_KEY=your_key`
   - Models: `gpt-4.1-mini` or `gpt-4o-mini`

2. **Anthropic Claude**
   - Strong at technical analysis
   - Requires Anthropic API key
   - Set in .env: `ANTHROPIC_API_KEY=your_key`
   - Models: `claude-3-5-haiku-latest`, `claude-sonnet-4-20250514`, or `claude-opus-4-1-20250805`

3. **Local Models via Ollama**
   - No API key required
   - Requires [Ollama](https://ollama.ai) installation
   - Supported models:
     - gemma3:4b (default)
     - LLaVA 13B
     - BakLLaVA
     - Other compatible multimodal models

### Installation

1. Clone the repository:
```powershell
git clone https://github.com/raylirui-self/mech-drawing-analyzer.git
Set-Location mech-drawing-analyzer  # or cd mech-drawing-analyzer
```

2. Set up the environment:

   Option A: Using conda (recommended):
   ```powershell
   conda env create -f environment.yml
   conda activate mech_drawing_expert
   ```

   Option B: Using pip:
   ```powershell
   python -m venv venv
   # Activate the virtual environment
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Set up environment variables:
```powershell
Copy-Item .env.example .env
# Edit .env with your API keys using your preferred editor
# For example:
notepad .env
```

### Running the Application

#### Option 1: Command Line
```powershell
python src/analyzer.py --image .\examples\mechanical_drawing.png --rules .\examples\sample_rules.json
```

#### Option 2: Python Script
```python
from src.analyzer import MechanicalDrawingAnalyzer

analyzer = MechanicalDrawingAnalyzer(llm_provider="openai")
results = analyzer.analyze_drawing("drawing.png")
print(results)
```

## 🎯 Usage Examples

## 📁 Project Structure

```
mech-drawing-analyzer/
├── .env                    # Your API keys (create from .env.example)
├── .env.example           # Template for environment variables
├── .gitignore            # Git ignore rules
├── LICENSE               # MIT License
├── README.md             # This documentation
├── CONTRIBUTING.md       # Contribution guidelines
├── requirements.txt      # Python dependencies
├── environment.yml       # Conda environment specification
├── setup.py             # Package installation script
├── src/
│   ├── __init__.py
│   ├── analyzer.py      # Core analysis logic
│   └── compliance_rules.py
└── examples/            # Example files
    ├── mechanical_drawing.png
    └── sample_rules.json


### Single Drawing Analysis
```python
from src.analyzer import MechanicalDrawingAnalyzer

# Initialize with your preferred model
analyzer = MechanicalDrawingAnalyzer(
    llm_provider="openai",  # or "claude", "ollama"
    model="gpt-4.1-mini"  # or another preferred model
)

# Analyze drawing
results = analyzer.analyze_drawing("examples/mechanical_drawing.png")

# Check compliance with design rules
violations = analyzer.check_compliance(results, {
    'min_wall_thickness': 2.0,  # mm
    'max_aspect_ratio': 10.0,
    'max_position_tolerance': 0.1  # mm
})

# Access structured data
print(f"Part Number: {results['specification'].part_number}")
print(f"Material: {results['specification'].material}")
print(f"Critical Dimensions: {len(results['specification'].critical_dimensions)}")
```

### Loading Custom Rules
```python
import json
from src.compliance_rules import load_compliance_rules

# Load rules from JSON
rules = load_compliance_rules("examples/sample_rules.json")

# Or define rules programmatically
rules = {
    'min_wall_thickness': 2.0,
    'max_aspect_ratio': 10.0,
    'max_position_tolerance': 0.1
}
    compliance_rules=compliance_rules,
    save_individual=True
)
```

## 🛠️ Configuration

### Supported Models

| Provider | Model | Requirements |
|----------|-------|--------------|
| OpenAI | GPT-4 | API key |
| Anthropic | Claude 3 | API key |
| Ollama | LLaVA 13B | Local GPU (8GB+ VRAM) |

### Compliance Rules

Define rules in JSON:
```json
{
  "text_rules": [
    "Minimum wall thickness: 2mm",
    "All holes must have position tolerance"
  ],
  "numeric_rules": {
    "min_wall_thickness": 2.0,
    "max_aspect_ratio": 10.0,
    "max_position_tolerance": 0.1
  }
}
```


## 📁 Project Structure

```
mech-drawing-analyzer/
├── src/                 # Core analysis modules
└── examples/           # Sample drawings and rules
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Acknowledgments

This project was developed with substantial assistance from Claude (Anthropic), an AI assistant that provided code architecture, implementation details, and technical guidance. The hybrid approach of combining traditional computer vision with large language models was designed through collaborative AI-human interaction.

### Key Technologies Used
- **OpenCV** for image preprocessing
- **LLMs** (GPT, Claude, LLaVA) for content understanding

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Known Issues/Constraints

- PDF support requires `poppler-utils` on Windows
- Local models require significant GPU memory (8GB+ recommended)
- Some GD&T symbols may require fine-tuning for accurate recognition
  - See **Roadmap** below
- **Unit conversion**: limited to IN to MM  
  - Assumes design rule uses MM
- Conflicting Numpy version between opencv and Gradio

## 🚀 Roadmap

- [ ] Enhance accuracy and consistency
  - [ ] Finetuning local model for better vision
  - [ ] others (TBD)
- [ ] Enhanced UI (Gradio or others)
- [ ] Support for 3D CAD file analysis
- [ ] Real-time drawing validation
- [ ] Support for hand-drawn sketches

---

**Disclaimer**: This tool is meant to assist in drawing analysis but should not replace human verification for critical applications. Always verify extracted dimensions and compliance checks for production use.
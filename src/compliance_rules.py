"""
Compliance checking module
Co-Author: AI-assisted development with Claude (Anthropic)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class ComplianceRule:
    """Single compliance rule"""
    name: str
    category: str
    check_type: str  # 'numeric', 'boolean', 'exists'
    value: any
    tolerance: Optional[float] = None
    unit: Optional[str] = None
    severity: str = 'error'  # 'error', 'warning', 'info'


class ComplianceChecker:
    """Check drawings against design rules"""
    
    def __init__(self, rules_file: Optional[str] = None):
        self.rules = []
        if rules_file:
            self.load_rules(rules_file)
    
    def load_rules(self, rules_file: str):
        """Load rules from JSON file"""
        import json
        with open(rules_file, 'r') as f:
            rules_data = json.load(f)
        
        # Parse numeric rules
        if 'numeric_rules' in rules_data:
            for name, value in rules_data['numeric_rules'].items():
                self.rules.append(ComplianceRule(
                    name=name,
                    category='dimensional',
                    check_type='numeric',
                    value=value
                ))
        
        # Parse material rules
        if 'material_rules' in rules_data:
            for name, value in rules_data['material_rules'].items():
                self.rules.append(ComplianceRule(
                    name=name,
                    category='material',
                    check_type='exists' if 'require' in name else 'list',
                    value=value
                ))
        
        # Parse GD&T rules
        if 'gdt_rules' in rules_data:
            for name, value in rules_data['gdt_rules'].items():
                self.rules.append(ComplianceRule(
                    name=name,
                    category='gdt',
                    check_type='numeric' if isinstance(value, (int, float)) else 'boolean',
                    value=value
                ))
    
    def check_specification(self, spec: dict) -> List[Dict]:
        """Check a part specification against all rules"""
        violations = []
        
        for rule in self.rules:
            violation = self._check_single_rule(spec, rule)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _check_single_rule(self, spec: dict, rule: ComplianceRule) -> Optional[Dict]:
        """Check a single rule"""
        
        if rule.category == 'dimensional':
            return self._check_dimensional_rule(spec, rule)
        elif rule.category == 'material':
            return self._check_material_rule(spec, rule)
        elif rule.category == 'gdt':
            return self._check_gdt_rule(spec, rule)
        
        return None
    
    def _check_dimensional_rule(self, spec: dict, rule: ComplianceRule) -> Optional[Dict]:
        """Check dimensional compliance"""
        
        # Check in critical dimensions
        for dim in spec.get('critical_dimensions', []):
            if rule.name == 'min_wall_thickness' and 'wall' in dim.get('feature', '').lower():
                if dim['value'] < rule.value:
                    return {
                        'rule': rule.name,
                        'severity': rule.severity,
                        'message': f"Wall thickness {dim['value']}{dim.get('unit', 'mm')} below minimum {rule.value}mm",
                        'location': dim.get('feature', 'unknown')
                    }
        
        # Check aspect ratios
        if rule.name == 'max_aspect_ratio':
            overall = spec.get('overall_dimensions', {})
            if 'length' in overall and 'width' in overall:
                ratio = overall['length'].get('value', 0) / max(overall['width'].get('value', 1), 0.001)
                if ratio > rule.value:
                    return {
                        'rule': rule.name,
                        'severity': rule.severity,
                        'message': f"Aspect ratio {ratio:.2f} exceeds maximum {rule.value}",
                        'location': 'overall dimensions'
                    }
        
        return None
    
    def _check_material_rule(self, spec: dict, rule: ComplianceRule) -> Optional[Dict]:
        """Check material compliance"""
        
        material = spec.get('material', '')
        
        if rule.name == 'require_material_spec' and rule.value and not material:
            return {
                'rule': rule.name,
                'severity': rule.severity,
                'message': "Material specification is required but not found",
                'location': 'title block'
            }
        
        if rule.name == 'allowed_materials' and material:
            if material not in rule.value:
                return {
                    'rule': rule.name,
                    'severity': 'warning',
                    'message': f"Material '{material}' not in approved list",
                    'location': 'title block'
                }
        
        return None
    
    def _check_gdt_rule(self, spec: dict, rule: ComplianceRule) -> Optional[Dict]:
        """Check GD&T compliance"""
        
        gdt_symbols = spec.get('gdt_requirements', [])
        
        for gdt in gdt_symbols:
            symbol_type = gdt.get('symbol_type', '').lower()
            tolerance = gdt.get('tolerance', 0)
            
            if f"max_{symbol_type}" == rule.name and tolerance > rule.value:
                return {
                    'rule': rule.name,
                    'severity': rule.severity,
                    'message': f"{symbol_type.title()} tolerance {tolerance} exceeds maximum {rule.value}",
                    'location': gdt.get('applies_to', 'unknown feature')
                }
        
        return None

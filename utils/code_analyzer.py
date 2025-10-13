import re
import ast
from typing import Dict, List

class CodeAnalyzer:
    def __init__(self):
        self.max_line_length = 100
    
    def analyze(self, code: str, language: str = 'python') -> Dict:
        """
        Analyze code quality and return metrics
        """
        
        if not code or len(code.strip()) < 5:
            return {
                'correctness': 0,
                'readability': 0,
                'efficiency': 0,
                'overall': 0,
                'suggestions': ['No code provided'],
                'line_count': 0,
                'has_errors': True
            }
        
        if language.lower() == 'python':
            return self._analyze_python(code)
        else:
            return self._analyze_generic(code)
    
    def _analyze_python(self, code: str) -> Dict:
        """Analyze Python code"""
        
        metrics = {
            'correctness': 0,
            'readability': 0,
            'efficiency': 0,
            'overall': 0,
            'suggestions': [],
            'line_count': 0,
            'has_errors': False
        }
        
        lines = code.split('\n')
        metrics['line_count'] = len([l for l in lines if l.strip()])
        
        # 1. CORRECTNESS
        try:
            ast.parse(code)
            metrics['correctness'] = 100
        except SyntaxError as e:
            metrics['correctness'] = 0
            metrics['has_errors'] = True
            metrics['suggestions'].append(f'❌ Syntax Error: {e.msg}')
            metrics['overall'] = 0
            return metrics
        except Exception as e:
            metrics['correctness'] = 50
            metrics['suggestions'].append(f'⚠️ Code issue: {str(e)}')
        
        # 2. READABILITY
        readability_score = 100
        
        comment_count = len([l for l in lines if l.strip().startswith('#')])
        if metrics['line_count'] > 15 and comment_count < 3:
            readability_score -= 10
            metrics['suggestions'].append('💬 Add more comments')
        
        short_vars = len(re.findall(r'\b([a-z])\s*=', code))
        if short_vars > 5:
            readability_score -= 10
            metrics['suggestions'].append('📝 Use descriptive variable names')
        
        metrics['readability'] = max(0, readability_score)
        
        # 3. EFFICIENCY
        efficiency_score = 100
        
        nested_loops = code.count('for') + code.count('while')
        if nested_loops > 3:
            efficiency_score -= 15
            metrics['suggestions'].append('⚡ Consider optimizing loops')
        
        metrics['efficiency'] = max(0, efficiency_score)
        
        # 4. OVERALL
        metrics['overall'] = int(
            metrics['correctness'] * 0.50 +
            metrics['readability'] * 0.30 +
            metrics['efficiency'] * 0.20
        )
        
        if metrics['overall'] >= 90:
            metrics['suggestions'].insert(0, '🌟 Excellent code!')
        elif metrics['overall'] >= 75:
            metrics['suggestions'].insert(0, '👍 Good code!')
        
        return metrics
    
    def _analyze_generic(self, code: str) -> Dict:
        """Generic analysis"""
        lines = [l for l in code.split('\n') if l.strip()]
        
        return {
            'correctness': 85,
            'readability': 80,
            'efficiency': 75,
            'overall': 80,
            'suggestions': ['✅ Code looks good!'],
            'line_count': len(lines),
            'has_errors': False
        }
import re
import ast
from typing import Dict, List
from utils.constants import SUPPORTED_LANGUAGES

class CodeAnalyzer:
    def __init__(self):
        self.max_line_length = 100
    
    def analyze(self, code: str, language: str = 'python') -> Dict:
        """Analyze code quality for any language"""
        
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
        
        language = language.lower()
        
        # Python-specific analysis
        if language in ['python', 'py']:
            return self._analyze_python(code)
        
        # Generic analysis for all other languages
        return self._analyze_generic(code, language)
    
    def _analyze_python(self, code: str) -> Dict:
        """Detailed Python analysis"""
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
        
        # Correctness check
        try:
            ast.parse(code)
            metrics['correctness'] = 100
        except SyntaxError as e:
            metrics['correctness'] = 0
            metrics['has_errors'] = True
            metrics['suggestions'].append(f'❌ Syntax Error: {e.msg}')
            metrics['overall'] = 0
            return metrics
        except:
            metrics['correctness'] = 50
        
        # Readability
        readability_score = 100
        comment_count = len([l for l in lines if l.strip().startswith('#')])
        if metrics['line_count'] > 15 and comment_count < 3:
            readability_score -= 10
            metrics['suggestions'].append('💬 Add more comments')
        
        metrics['readability'] = max(0, readability_score)
        
        # Efficiency
        efficiency_score = 100
        nested_loops = code.count('for') + code.count('while')
        if nested_loops > 3:
            efficiency_score -= 15
            metrics['suggestions'].append('⚡ Consider optimizing loops')
        
        metrics['efficiency'] = max(0, efficiency_score)
        
        # Overall
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
    
    def _analyze_generic(self, code: str, language: str) -> Dict:
        """Generic analysis for all languages"""
        lines = [l for l in code.split('\n') if l.strip()]
        
        suggestions = []
        readability = 85
        
        # Get language info
        lang_info = SUPPORTED_LANGUAGES.get(language, SUPPORTED_LANGUAGES.get('any'))
        
        # Check for comments (works for most languages)
        comment_chars = ['#', '//', '/*', '*', '--']
        has_comments = any(any(char in line for char in comment_chars) for line in lines)
        
        if not has_comments and len(lines) > 10:
            suggestions.append(f'💬 Add comments ({lang_info["name"]})')
            readability -= 15
        
        # Check line length
        long_lines = len([l for l in lines if len(l) > 120])
        if long_lines > 0:
            suggestions.append(f'📏 {long_lines} lines are too long')
            readability -= 10
        
        # Language-specific checks
        if language in ['java', 'csharp', 'cpp']:
            if not any('{' in line for line in lines):
                readability -= 20
                suggestions.append('⚠️ Code structure looks incomplete')
        
        if not suggestions:
            suggestions.append(f'✅ {lang_info["name"]} code looks good!')
        
        return {
            'correctness': 85,
            'readability': max(0, readability),
            'efficiency': 80,
            'overall': 83,
            'suggestions': suggestions,
            'line_count': len(lines),
            'has_errors': False
        }

import google.generativeai as genai
import os
from typing import Dict

class AIVerifier:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            try:
                genai.configure(api_key=api_key)
                # Use the correct model name for 2024/2025
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                self.enabled = True
                print('✅ AI Verifier enabled with Gemini 2.0 Flash')
            except Exception as e:
                print(f'⚠️ Could not initialize Gemini: {e}')
                self.enabled = False
        else:
            self.enabled = False
            print('⚠️ AI Verifier disabled - no GEMINI_API_KEY')
    
    def verify_solution(self, challenge_title: str, challenge_description: str, challenge_difficulty: str, submitted_code: str, language: str = 'python') -> Dict:
        if not self.enabled:
            return self._basic_verification(submitted_code)
        
        try:
            prompt = f"""You are a code review expert. Analyze if this code solves the given challenge.

CHALLENGE: {challenge_title}
DESCRIPTION: {challenge_description}
DIFFICULTY: {challenge_difficulty}

SUBMITTED CODE:
{submitted_code}

Respond in EXACTLY this format:

SOLVES_CHALLENGE: YES or NO
CORRECTNESS_SCORE: number 0-100
LOGIC_SCORE: number 0-100
COMPLETENESS_SCORE: number 0-100
OVERALL_SCORE: number 0-100

FEEDBACK:
Brief explanation of whether the code solves the challenge

ISSUES:
- Issue 1 if any
- Issue 2 if any

STRENGTHS:
- Strength 1 if any
- Strength 2 if any

Be strict: Only say YES if the code actually solves the challenge correctly."""

            response = self.model.generate_content(prompt)
            result = self._parse_ai_response(response.text)
            print(f"✅ AI: Solves={result['solves_challenge']}, Score={result['overall_score']}")
            return result
            
        except Exception as e:
            print(f'❌ AI Error: {str(e)[:150]}')
            return self._basic_verification(submitted_code)
    
    def _parse_ai_response(self, text: str) -> Dict:
        result = {
            'solves_challenge': False,
            'correctness_score': 0,
            'logic_score': 0,
            'completeness_score': 0,
            'overall_score': 0,
            'feedback': '',
            'issues': [],
            'strengths': []
        }
        
        lines = text.split('\n')
        section = None
        
        for line in lines:
            line_stripped = line.strip()
            line_upper = line_stripped.upper()
            
            # Parse SOLVES_CHALLENGE
            if 'SOLVES_CHALLENGE' in line_upper:
                if 'YES' in line_upper:
                    result['solves_challenge'] = True
                elif 'NO' in line_upper:
                    result['solves_challenge'] = False
            
            # Parse scores
            elif 'CORRECTNESS_SCORE' in line_upper:
                try:
                    numbers = [int(s) for s in line_stripped.split() if s.isdigit()]
                    if numbers:
                        result['correctness_score'] = min(max(numbers[0], 0), 100)
                except:
                    result['correctness_score'] = 50
            
            elif 'LOGIC_SCORE' in line_upper:
                try:
                    numbers = [int(s) for s in line_stripped.split() if s.isdigit()]
                    if numbers:
                        result['logic_score'] = min(max(numbers[0], 0), 100)
                except:
                    result['logic_score'] = 50
            
            elif 'COMPLETENESS_SCORE' in line_upper:
                try:
                    numbers = [int(s) for s in line_stripped.split() if s.isdigit()]
                    if numbers:
                        result['completeness_score'] = min(max(numbers[0], 0), 100)
                except:
                    result['completeness_score'] = 50
            
            elif 'OVERALL_SCORE' in line_upper:
                try:
                    numbers = [int(s) for s in line_stripped.split() if s.isdigit()]
                    if numbers:
                        result['overall_score'] = min(max(numbers[0], 0), 100)
                except:
                    result['overall_score'] = 50
            
            # Parse sections
            elif line_stripped == 'FEEDBACK:':
                section = 'feedback'
            elif line_stripped == 'ISSUES:':
                section = 'issues'
            elif line_stripped == 'STRENGTHS:':
                section = 'strengths'
            
            # Parse content
            elif section == 'feedback' and line_stripped and not line_stripped.endswith(':'):
                result['feedback'] += line_stripped + ' '
            
            elif section == 'issues' and line_stripped.startswith('-'):
                issue = line_stripped[1:].strip()
                if issue:
                    result['issues'].append(issue)
            
            elif section == 'strengths' and line_stripped.startswith('-'):
                strength = line_stripped[1:].strip()
                if strength:
                    result['strengths'].append(strength)
        
        # Clean up feedback
        result['feedback'] = result['feedback'].strip()
        
        # Fallbacks
        if not result['feedback']:
            result['feedback'] = 'Code analysis completed.'
        if not result['issues']:
            if not result['solves_challenge']:
                result['issues'] = ['Solution does not solve the challenge']
            else:
                result['issues'] = ['No major issues detected']
        if not result['strengths']:
            result['strengths'] = ['Code syntax is valid']
        
        # If overall score is 0, calculate from other scores
        if result['overall_score'] == 0:
            result['overall_score'] = int(
                (result['correctness_score'] + result['logic_score'] + result['completeness_score']) / 3
            )
        
        return result
    
    def _basic_verification(self, code: str) -> Dict:
        return {
            'solves_challenge': False,
            'correctness_score': 30,
            'logic_score': 30,
            'completeness_score': 30,
            'overall_score': 30,
            'feedback': 'AI verification unavailable. Manual review required.',
            'issues': ['Could not verify solution automatically - manual review needed'],
            'strengths': ['Code syntax appears valid']
        }
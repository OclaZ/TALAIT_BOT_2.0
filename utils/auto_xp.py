from typing import Dict

class AutoXPCalculator:
    def __init__(self):
        self.base_participation_xp = 2
        self.max_quality_bonus = 6
        self.max_early_bonus = 2
        
    def calculate(
        self,
        code_quality: int,
        submission_number: int,
        total_lines: int,
        solves_challenge: bool = True,
        ai_overall_score: int = None
    ) -> Dict:
        quality_score = ai_overall_score if ai_overall_score is not None else code_quality
        
        if not solves_challenge:
            return {
                'total_xp': 1,
                'base_xp': 1,
                'quality_bonus': 0,
                'early_bonus': 0,
                'effort_bonus': 0,
                'penalty': -1,
                'breakdown': '⚠️ Solution does not solve the challenge\n❌ Reduced XP: +1 XP (participation only)'
            }
        
        base_xp = self.base_participation_xp
        
        if quality_score >= 90:
            quality_bonus = 6
        elif quality_score >= 80:
            quality_bonus = 5
        elif quality_score >= 70:
            quality_bonus = 4
        elif quality_score >= 60:
            quality_bonus = 3
        elif quality_score >= 50:
            quality_bonus = 2
        else:
            quality_bonus = 1
        
        if submission_number == 1:
            early_bonus = 2
        elif submission_number <= 5:
            early_bonus = 1
        else:
            early_bonus = 0
        
        effort_bonus = 1 if total_lines >= 50 else 0
        
        total_xp = base_xp + quality_bonus + early_bonus + effort_bonus
        
        breakdown_parts = [f'🎯 Base: +{base_xp} XP']
        
        if quality_bonus > 0:
            breakdown_parts.append(f'🤖 AI Score ({quality_score}/100): +{quality_bonus} XP')
        
        if early_bonus > 0:
            breakdown_parts.append(f'⚡ Early (#{submission_number}): +{early_bonus} XP')
        
        if effort_bonus > 0:
            breakdown_parts.append(f'💪 Effort ({total_lines} lines): +{effort_bonus} XP')
        
        return {
            'total_xp': total_xp,
            'base_xp': base_xp,
            'quality_bonus': quality_bonus,
            'early_bonus': early_bonus,
            'effort_bonus': effort_bonus,
            'penalty': 0,
            'breakdown': '\n'.join(breakdown_parts)
        }
# XP Values
XP_VALUES = {
    '1st': 10,
    '2nd': 7,
    '3rd': 5,
    'participation': 2
}

# Data files
DATA_DIR = 'data'
LEADERBOARD_FILE = 'leaderboard.json'
HALL_OF_FAME_FILE = 'hall_of_fame.json'
CHALLENGES_FILE = 'challenges.json'

# Role permissions
ALLOWED_ROLES = ['formateur', 'admin', 'moderator']

# Channel names
EXERCISE_CHANNEL_NAME = 'exercice'
SUBMISSION_CHANNEL_NAME = 'code-wars-submissions'

# Supported Programming Languages
SUPPORTED_LANGUAGES = {
    'python': {
        'name': 'Python',
        'emoji': '🐍',
        'extensions': ['.py'],
        'example': 'def hello():\n    print("Hello World")',
        'code_block': 'python'
    },
    'javascript': {
        'name': 'JavaScript',
        'emoji': '📜',
        'extensions': ['.js'],
        'example': 'function hello() {\n    console.log("Hello World");\n}',
        'code_block': 'javascript'
    },
    'java': {
        'name': 'Java',
        'emoji': '☕',
        'extensions': ['.java'],
        'example': 'public class Hello {\n    public static void main(String[] args) {\n        System.out.println("Hello World");\n    }\n}',
        'code_block': 'java'
    },
    'cpp': {
        'name': 'C++',
        'emoji': '⚡',
        'extensions': ['.cpp', '.cc', '.cxx'],
        'example': '#include <iostream>\nint main() {\n    std::cout << "Hello World";\n    return 0;\n}',
        'code_block': 'cpp'
    },
    'c': {
        'name': 'C',
        'emoji': '🔧',
        'extensions': ['.c'],
        'example': '#include <stdio.h>\nint main() {\n    printf("Hello World");\n    return 0;\n}',
        'code_block': 'c'
    },
    'csharp': {
        'name': 'C#',
        'emoji': '💎',
        'extensions': ['.cs'],
        'example': 'using System;\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello World");\n    }\n}',
        'code_block': 'csharp'
    },
    'go': {
        'name': 'Go',
        'emoji': '🔷',
        'extensions': ['.go'],
        'example': 'package main\nimport "fmt"\nfunc main() {\n    fmt.Println("Hello World")\n}',
        'code_block': 'go'
    },
    'rust': {
        'name': 'Rust',
        'emoji': '🦀',
        'extensions': ['.rs'],
        'example': 'fn main() {\n    println!("Hello World");\n}',
        'code_block': 'rust'
    },
    'php': {
        'name': 'PHP',
        'emoji': '🐘',
        'extensions': ['.php'],
        'example': '<?php\necho "Hello World";\n?>',
        'code_block': 'php'
    },
    'ruby': {
        'name': 'Ruby',
        'emoji': '💎',
        'extensions': ['.rb'],
        'example': 'puts "Hello World"',
        'code_block': 'ruby'
    },
    'swift': {
        'name': 'Swift',
        'emoji': '🦅',
        'extensions': ['.swift'],
        'example': 'print("Hello World")',
        'code_block': 'swift'
    },
    'kotlin': {
        'name': 'Kotlin',
        'emoji': '🎯',
        'extensions': ['.kt'],
        'example': 'fun main() {\n    println("Hello World")\n}',
        'code_block': 'kotlin'
    },
    'typescript': {
        'name': 'TypeScript',
        'emoji': '📘',
        'extensions': ['.ts'],
        'example': 'function hello(): void {\n    console.log("Hello World");\n}',
        'code_block': 'typescript'
    },
    'sql': {
        'name': 'SQL',
        'emoji': '🗃️',
        'extensions': ['.sql'],
        'example': 'SELECT * FROM users;',
        'code_block': 'sql'
    },
    'any': {
        'name': 'Any Language',
        'emoji': '🌐',
        'extensions': [],
        'example': 'Use any programming language',
        'code_block': 'text'
    }
}

def get_language_choices():
    """Get language choices for Discord slash commands"""
    return [
        {'name': f"{lang['emoji']} {lang['name']}", 'value': key}
        for key, lang in SUPPORTED_LANGUAGES.items()
    ]
import openai
from .config import OPENAI_CONFIG

openai.api_key = OPENAI_CONFIG['api_key']

def generate_response(content):
    """Generate a response using OpenAI API"""
    try:
        response = openai.chat.completions.create(
            model=OPENAI_CONFIG['model'],
            messages=[
                {"role": "system", "content": "You are a crypto enthusiast. Keep responses EXTREMELY brief - max 2 sentences. Be direct and concise."},
                {"role": "user", "content": f"Give a quick thought about this crypto topic (mention Solana if relevant): {content}"}
            ],
            max_tokens=OPENAI_CONFIG['max_tokens'],
            temperature=OPENAI_CONFIG['temperature']
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

def check_quota():
    """Check OpenAI API quota status"""
    try:
        response = openai.chat.completions.create(
            model=OPENAI_CONFIG['model'],
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        return True, response
    except Exception as e:
        return False, str(e)

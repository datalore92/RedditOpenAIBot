import openai
from .config import OPENAI_CONFIG

openai.api_key = OPENAI_CONFIG['api_key']

def generate_response(content, context=None, log=None):  # Added log parameter
    """Generate a response using OpenAI API"""
    try:
        base_personality = "You are a crypto enthusiast. Keep responses EXTREMELY brief - max 2 sentences. Be irreverent, everything in lower-case, and don't use periods"
        
        if context:
            personality = f"{base_personality}. {context}"
        else:
            personality = base_personality
            
        response = openai.chat.completions.create(
            model=OPENAI_CONFIG['model'],
            messages=[
                {"role": "system", "content": personality},
                {"role": "user", "content": f"Give a quick thought about this topic: {content}"}
            ],
            max_tokens=OPENAI_CONFIG['max_tokens'],
            temperature=OPENAI_CONFIG['temperature']
        )
        return response.choices[0].message.content
    except Exception as e:
        if log:
            log("✗ Error generating response: %s", str(e))
        else:
            print(f"Error generating response: {e}")
        return None

def check_quota(log=None):
    """Check OpenAI API quota status"""
    try:
        response = openai.chat.completions.create(
            model=OPENAI_CONFIG['model'],
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        
        if log:
            log("\n=== OpenAI API Status ===")
            log("✓ API Connection: Active")
            log(f"✓ Model: {response.model}")
            
            if hasattr(response, 'usage'):
                log("\nUsage Information:")
                log(f"→ Prompt tokens: {response.usage.prompt_tokens}")
                log(f"→ Completion tokens: {response.usage.completion_tokens}")
                log(f"→ Total tokens: {response.usage.total_tokens}")
        
        return True
        
    except openai.RateLimitError as e:
        if log:
            log("\n=== OpenAI API Status ===")
            log("✗ Rate limit exceeded")
            log(f"Error details: {str(e)}")
        return False
    except Exception as e:
        if log:
            log("\n=== OpenAI API Status ===")
            log(f"✗ Error checking quota: {str(e)}")
        return False

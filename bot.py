import praw
import openai
import os
import time
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import re
import json

# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure Reddit
reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT'),
    username=os.getenv('REDDIT_USERNAME'),
    password=os.getenv('REDDIT_PASSWORD')
)

# Subreddits to monitor
SUBREDDITS = [
    'CryptoMoonShots',
    'altcoin',
    'CryptoMarkets',
    'NFTsMarketplace',
    'NFT',
    'solana',
    'SolanaNFT'
]

# Keywords to look for
KEYWORDS = [
    'altcoin',
    'shitcoin',
    'nft',
    'new coin',
    'moonshot',
    'solana',
    'sol'
]

def generate_response(content):
    """Generate a response using OpenAI API"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a crypto enthusiast. Keep responses EXTREMELY brief - max 2 sentences. Be direct and concise."},
                {"role": "user", "content": f"Give a quick thought about this crypto topic (mention Solana if relevant): {content}"}
            ],
            max_tokens=40,  # Even shorter responses
            temperature=0.7  # Keep responses varied
        )
        return response.choices[0].message.content
    except openai.RateLimitError as e:
        print("\n=== OpenAI API Status ===")
        print("✗ Rate limit exceeded")
        print(f"Error details: {str(e)}")
        return None
    except Exception as e:
        print(f"Error generating response: {e}")
        return None

def should_respond(text):
    """Check if the text contains relevant keywords"""
    text = text.lower()
    found_keywords = [keyword for keyword in KEYWORDS if keyword.lower() in text]
    if found_keywords:
        print("→ Keywords found:", ', '.join(found_keywords))
    return len(found_keywords) > 0

def parse_time_string(time_str):
    """Convert time string to seconds"""
    time_units = {
        'ms': 0.001,
        's': 1,
        'm': 60,
        'h': 3600,
    }
    parts = re.findall(r'(\d+)([a-z]+)', time_str.lower())
    return sum(float(value) * time_units[unit] for value, unit in parts)

def format_time_remaining(seconds):
    """Format seconds into readable time"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"

def check_openai_quota():
    """Check OpenAI API quota status with detailed information"""
    try:
        # Make a test request to check API status
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        
        print("\n=== OpenAI API Status ===")
        print("✓ API Connection: Active")
        print(f"✓ Model: {response.model}")
        
        # Get API configuration info
        print("\nAPI Configuration:")
        print(f"→ Base URL: {openai.api_base}")
        print(f"→ Organization: {openai.organization or 'default'}")
        
        # Try to access usage information from the response
        if hasattr(response, 'usage'):
            print("\nRequest Usage:")
            print(f"→ Prompt tokens: {response.usage.prompt_tokens}")
            print(f"→ Completion tokens: {response.usage.completion_tokens}")
            print(f"→ Total tokens: {response.usage.total_tokens}")
        
        # Get response timing
        if hasattr(response, '_response_ms'):
            print(f"\nPerformance:")
            print(f"→ Response time: {response._response_ms}ms")

        return True

    except openai.RateLimitError as e:
        print("\n=== OpenAI API Status ===")
        print("✗ Rate limit exceeded")
        print(f"Error details: {str(e)}")
        return False
    
    except Exception as e:
        print("\n=== OpenAI API Status ===")
        print(f"✗ Error Type: {type(e).__name__}")
        print(f"✗ Error Details: {str(e)}")
        if isinstance(e, openai.AuthenticationError):
            print("→ Please check your API key")
        elif isinstance(e, openai.InvalidRequestError):
            print("→ Invalid request parameters")
        return False

def has_bot_activity(submission):
    """Check if bot has ANY activity in this submission thread"""
    try:
        # Get bot's username
        bot_username = reddit.user.me().name
        
        # Flatten all comments to check them
        submission.comments.replace_more(limit=None)
        all_comments = submission.comments.list()
        
        # Check if any comment in the thread is from the bot
        return any(
            comment.author and comment.author.name == bot_username 
            for comment in all_comments
        )
    except Exception as e:
        print(f"Error checking thread history: {e}")
        return True  # Skip thread if we can't check properly

def monitor_reddit():
    """Monitor Reddit for relevant posts and comments"""
    last_quota_check = 0
    check_interval = 60
    
    print("\n=== Bot Status ===")
    print("✓ Monitoring subreddits:", ", ".join(SUBREDDITS))
    print("✓ Looking for keywords:", ", ".join(KEYWORDS))
    print("\nMonitoring for new posts and comments...")
    print("Press Ctrl+C to stop the bot\n")
    
    while True:
        try:
            print("\nConnecting to Reddit stream...", end='\r')
            subreddit = reddit.subreddit('+'.join(SUBREDDITS))
            
            # Debug: Print authentication status
            print(f"Bot authenticated as: u/{reddit.user.me().name}")
            
            # Monitor new submissions only
            print("Waiting for new posts...\n")
            for submission in subreddit.stream.submissions(skip_existing=True):  # Changed to True
                # Only process submissions less than 1 hour old for extra safety
                submission_age = datetime.utcnow().timestamp() - submission.created_utc
                if submission_age > 3600:  # Skip if older than 1 hour
                    continue
                
                current_time = datetime.fromtimestamp(submission.created_utc)
                print(f"\n{'='*50}")
                print(f"Found new post in r/{submission.subreddit.display_name}")  # Added 'new' for clarity
                print(f"Age: {int(submission_age/60)} minutes old")  # Show how old the post is
                
                print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Title: {submission.title}")
                print(f"Author: u/{submission.author}")
                print(f"URL: https://reddit.com{submission.permalink}")
                
                # Check for any bot activity in thread first
                if has_bot_activity(submission):
                    print("→ Bot has already participated in this thread - skipping entirely")
                    continue
                
                if should_respond(submission.title + submission.selftext):
                    print("✓ Keywords detected - Generating response...")
                    response = generate_response(submission.title + "\n" + submission.selftext)
                    
                    if response:
                        try:
                            comment = submission.reply(response)
                            print(f"✓ Successfully posted response in r/{submission.subreddit.display_name}")
                            print(f"→ Comment link: https://reddit.com{comment.permalink}")
                            print("Waiting 60s to avoid rate limits...")
                            time.sleep(60)
                        except Exception as e:
                            print(f"✗ Error posting response: {e}")

                # Only check comments if we haven't posted in thread at all
                print(f"Checking submission comments in r/{submission.subreddit.display_name}...")
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list():
                    if should_respond(comment.body):
                        print("→ Found relevant comment to respond to")
                        print("→ Generating AI response...")
                        response = generate_response(comment.body)
                        if response:
                            try:
                                reply = comment.reply(response)
                                print(f"✓ Successfully posted comment response in r/{submission.subreddit.display_name}")
                                print(f"→ Reply link: https://reddit.com{reply.permalink}")
                                print("Waiting 60s to avoid rate limits...")
                                time.sleep(60)
                            except Exception as e:
                                print(f"✗ Error posting comment: {e}")
                
                print("\nResuming submission monitoring...\n")
                
        except KeyboardInterrupt:
            print("\n\nCtrl+C detected. Shutting down gracefully...")
            return
        except Exception as e:
            print(f"\n✗ Error in monitoring loop: {e}")
            print("Waiting 60s before retry...")
            time.sleep(60)

if __name__ == "__main__":
    print("=== Reddit Solana Bot Starting ===")
    print("Time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        monitor_reddit()
    except KeyboardInterrupt:
        print("\n\nCtrl+C detected. Shutting down gracefully...")
    except Exception as e:
        print(f"\nCritical error in main loop: {e}")
    finally:
        print("Bot stopped successfully.")

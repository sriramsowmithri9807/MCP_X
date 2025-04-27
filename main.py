from mcp.server.fastmcp import FastMCP
import tweepy
import os
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime


mcp = FastMCP("X (Twitter) MCP Server")

# Data models
@dataclass
class Tweet:
    id: str
    content: str
    author: str
    timestamp: datetime
    likes: int = 0
    retweets: int = 0
    replies: List[str] = None

    def __post_init__(self):
        if self.replies is None:
            self.replies = []


tweets_db = {}
tweet_counter = 0


TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

def get_twitter_client() -> tweepy.Client:
    """Initialize and return the Twitter API client"""
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        raise ValueError("Twitter API credentials not found in environment variables")
    
    client = tweepy.Client(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
    )
    return client

@mcp.tool()
def post_tweet(content: str) -> Dict:
    """
    Post a new tweet to your X account.
    
    Args:
        content (str): The content of the tweet (max 280 characters)
    
    Returns:
        dict: Details of the created tweet
    """
    try:
        if len(content) > 280:
            return {"error": "Tweet content exceeds 280 characters"}
        
        client = get_twitter_client()
        tweet = client.create_tweet(text=content)
        
        return {
            "status": "success",
            "tweet_id": tweet.data['id'],
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def reply_to_tweet(tweet_id: str, content: str) -> Dict:
    """
    Reply to an existing tweet.
    
    Args:
        tweet_id (str): The ID of the tweet to reply to
        content (str): The content of the reply (max 280 characters)
    
    Returns:
        dict: Details of the created reply
    """
    try:
        if len(content) > 280:
            return {"error": "Reply content exceeds 280 characters"}
        
        client = get_twitter_client()
        reply = client.create_tweet(
            text=content,
            in_reply_to_tweet_id=tweet_id
        )
        
        return {
            "status": "success",
            "reply_id": reply.data['id'],
            "original_tweet_id": tweet_id,
            "content": content
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_tweet(tweet_id: str) -> Dict:
    """
    Get details of a specific tweet.
    
    Args:
        tweet_id (str): The ID of the tweet to retrieve
    
    Returns:
        dict: Details of the tweet
    """
    try:
        client = get_twitter_client()
        tweet = client.get_tweet(
            tweet_id,
            expansions=['author_id'],
            tweet_fields=['created_at', 'public_metrics']
        )
        
        if not tweet.data:
            return {"error": "Tweet not found"}
        
        return {
            "tweet_id": tweet.data.id,
            "content": tweet.data.text,
            "created_at": str(tweet.data.created_at),
            "metrics": tweet.data.public_metrics
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def like_tweet(tweet_id: str) -> Dict:
    """
    Like a tweet.
    
    Args:
        tweet_id (str): The ID of the tweet to like
    
    Returns:
        dict: Status of the like operation
    """
    try:
        client = get_twitter_client()
        client.like(tweet_id)
        return {
            "status": "success",
            "message": f"Successfully liked tweet {tweet_id}"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def retweet(tweet_id: str) -> Dict:
    """
    Retweet a tweet.
    
    Args:
        tweet_id (str): The ID of the tweet to retweet
    
    Returns:
        dict: Status of the retweet operation
    """
    try:
        client = get_twitter_client()
        client.retweet(tweet_id)
        return {
            "status": "success",
            "message": f"Successfully retweeted tweet {tweet_id}"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_tweet_thread(tweet_id: str) -> dict:
    """
    Get a tweet and all its replies as a thread.
    
    Args:
        tweet_id (str): The ID of the tweet to get the thread for
    
    Returns:
        dict: Thread containing the original tweet and all replies
    """
    if tweet_id not in tweets_db:
        return {"error": f"Tweet with ID {tweet_id} not found"}
    
    tweet = tweets_db[tweet_id]
    thread = {
        "original_tweet": {
            "tweet_id": tweet.id,
            "content": tweet.content,
            "author": tweet.author,
            "timestamp": tweet.timestamp.isoformat(),
            "likes": tweet.likes,
            "retweets": tweet.retweets
        },
        "replies": []
    }
    
    for reply_id in tweet.replies:
        if reply_id in tweets_db:
            reply = tweets_db[reply_id]
            thread["replies"].append({
                "tweet_id": reply.id,
                "content": reply.content,
                "author": reply.author,
                "timestamp": reply.timestamp.isoformat(),
                "likes": reply.likes,
                "retweets": reply.retweets
            })
    
    return thread

@mcp.tool()
def search_tweets(query: str) -> List[dict]:
    """
    Search for tweets containing the given query string.
    
    Args:
        query (str): The search query string
    
    Returns:
        List[dict]: List of matching tweets
    """
    results = []
    for tweet in tweets_db.values():
        if query.lower() in tweet.content.lower():
            results.append({
                "tweet_id": tweet.id,
                "content": tweet.content,
                "author": tweet.author,
                "timestamp": tweet.timestamp.isoformat(),
                "likes": tweet.likes,
                "retweets": tweet.retweets
            })
    return results

if __name__ == "__main__":
    mcp.run()
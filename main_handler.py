import json
import logging
from typing import Dict, Any
from brainstorm_engine import BrainstormEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize a global BrainstormEngine instance
try:
    engine = BrainstormEngine()
    logger.info("BrainstormEngine initialized successfully")
except Exception as e:
    logger.error(f"BrainstormEngine initialization failed: {e}")
    engine = None


def handle_brainstorm_request(request_json: dict) -> dict:
    """
    Main entry for handling a brainstorming request.
    Args:
        request_json: Dict with request parameters. Must include "topic".
                      Optional: "user_id", "num_ideas".
    Returns:
        A dict containing the result list or an error message.
    """
    if engine is None:
        return {"error": "System initialization failed. Please contact the administrator.", "success": False}
    
    # Parameter validation and extraction
    topic = request_json.get("topic", "").strip()
    user_id = request_json.get("user_id")
    num_ideas = request_json.get("num_ideas", 5)
    
    # Input validation
    if not topic:
        return {"error": "Missing required parameter 'topic' or topic is empty.", "success": False}
    
    if not isinstance(num_ideas, int) or num_ideas < 1 or num_ideas > 20:
        return {"error": "Parameter 'num_ideas' must be an integer between 1 and 20.", "success": False}
    
    # Log the request
    logger.info(f"Processing brainstorming request — topic: {topic}, user: {user_id}, count: {num_ideas}")
    
    try:
        # Execute brainstorming
        results = engine.brainstorm(topic, user_id=user_id, num_ideas=num_ideas)
        
        # Format the response
        formatted_results = []
        for i, idea in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "idea": idea.get("idea", ""),
                "detail": idea.get("detail", ""),
                "model_score": idea.get("model_score", 0),
                "user_score": idea.get("user_score", 0),
                "total_score": idea.get("total_score", 0),
                "evaluation_detail": idea.get("evaluation_detail", "")
            })
        
        logger.info(f"Brainstorming completed — generated {len(formatted_results)} ideas")
        
        return {
            "success": True,
            "ideas": formatted_results,
            "metadata": {
                "topic": topic,
                "user_id": user_id,
                "total_count": len(formatted_results)
            }
        }
        
    except Exception as e:
        error_msg = f"Brainstorming execution failed: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg, "success": False}


def validate_request_format(request_data: Any) -> Dict[str, Any]:
    """
    Validate the request format.
    """
    if not isinstance(request_data, dict):
        return {"error": "Request data must be a JSON object.", "success": False}
    
    return {"success": True}


# Simple CLI for testing when run as a script
if __name__ == "__main__":
    print("=== Brainstorming System Test ===")
    
    while True:
        print("\nEnter test parameters (type 'quit' to exit):")
        topic = input("Topic: ").strip()
        
        if topic.lower() == 'quit':
            break
            
        if not topic:
            print("Topic cannot be empty")
            continue
            
        user_id = input("User ID (optional): ").strip() or None
        
        try:
            num_ideas = int(input("Number of ideas (default 5): ") or "5")
        except ValueError:
            num_ideas = 5
        
        # Build request
        test_request = {
            "topic": topic,
            "user_id": user_id,
            "num_ideas": num_ideas
        }
        
        print(f"\nExecuting request: {test_request}")
        print("-" * 50)
        
        # Handle request
        result = handle_brainstorm_request(test_request)
        
        if result.get("success"):
            print(f"✅ Successfully generated {len(result['ideas'])} ideas:")
            for idea in result["ideas"]:
                print(f"\n🔥 Rank: {idea['rank']}")
                print(f"💡 Idea: {idea['idea']}")
                print(f"📊 Score: {idea['total_score']:.2f} (model: {idea['model_score']}, user: {idea['user_score']})")
                print(f"📝 Detail: {idea['detail'][:200]}...")
        else:
            print(f"❌ Error: {result['error']}")
        
        print("=" * 80)
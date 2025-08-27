import re
from typing import List, Dict, Optional
from model_adapters import DoubaoAdapter, ChatGPTAdapter, GeminiAdapter
from user_profile import UserProfile
from config import Config

class BrainstormEngine:
    def __init__(self, model1_adapter=None, model2_adapter=None, model3_adapter=None):
        # Initialize three model adapters
        self.model1 = model1_adapter or DoubaoAdapter()      # Idea generation
        self.model2 = model2_adapter or ChatGPTAdapter()     # Plan refinement
        self.model3 = model3_adapter or GeminiAdapter()      # Quality evaluation
        
        self.user_profile = UserProfile()
    
    def brainstorm(self, topic: str, user_id: str = None, num_ideas: int = 5) -> list:
        """
        End-to-end brainstorming:
        1) Build user context
        2) Generate raw ideas (Doubao)
        3) Expand each idea into an executable plan (ChatGPT)
        4) Score & filter (Gemini)
        5) Sort by model score and return top N
        """
        # 1. Build user context
        user_context = "General user, no specific preferences"
        user_behavior = "No historical behavior data"
        constraints = "No special constraints"
        
        if user_id:
            user_history = self.user_profile.get_user_history(user_id)
            if user_history:
                interests = user_history.get("interest_keywords", [])
                recent_topics = user_history.get("recent_topics", [])
                
                if interests:
                    user_context = f"User interests: {', '.join(interests[:5])}"  # take top-5 interests
                if recent_topics:
                    user_behavior = f"Recently followed topics: {', '.join(recent_topics[-3:])}"  # take last-3 topics
        
        # 2. Generate initial ideas (using Doubao)
        prompt1 = f"""You are a master of creativity who provides unique and practical ideas for users.

**Topic**: {topic}
**User Background**: {user_context}
**Behavior Pattern**: {user_behavior}
**Constraints**: {constraints}

Please provide {num_ideas * 2} creative ideas. Requirements:
1. **Highly practical** — each idea must be actionable
2. **Innovative & distinctive** — avoid clichés; personalize to the user's traits
3. **Varied levels** — include options with different difficulty and effort levels

Output format (numbered list only, one idea per line, no extra explanation):
1. [Specific idea]
2. [Specific idea]
3. [Specific idea]
..."""

        try:
            initial_output = self.model1.generate_text(prompt1, temperature=0.8)
        except Exception as e:
            raise RuntimeError(f"Model 1 failed to generate ideas: {e}")
        
        # Parse generated ideas
        ideas = self._parse_ideas_from_output(initial_output)
        if not ideas:
            raise RuntimeError("Failed to parse valid ideas from the model output.")
        
        # 3. Expand each idea with details (using ChatGPT)
        expanded_ideas = []
        for idea in ideas[:num_ideas * 2]:  # process more candidate ideas
            prompt2 = f"""You are a professional execution expert who turns creative ideas into actionable project plans.

Original Topic: {topic}
Idea Concept: {idea}

Please expand this idea with:
1. Concrete implementation steps (3–5 key steps)
2. Required resources and conditions
3. Expected timeline
4. Potential risks/challenges and mitigation strategies
5. Expected outcomes and benefits

Write in a structured and practical format to ensure the plan is actionable."""
            
            try:
                detailed_text = self.model2.generate_text(
                    prompt2,
                    system_prompt="You are an experienced project execution specialist who translates ideas into feasible plans.",
                    temperature=0.6
                )
            except Exception as e:
                print(f"Failed to expand idea: {e}")
                detailed_text = idea  # fallback to raw idea when expansion fails
                
            expanded_ideas.append({
                "idea": idea,
                "detail": detailed_text
            })
        
        # 4. Score and filter ideas (using Gemini)
        filtered_ideas = []
        for item in expanded_ideas:
            idea_text = item["detail"]
            idea_concept = item["idea"]
            
            prompt3 = f"""You are a professional idea evaluation expert. Please provide an objective score.

**To Evaluate**:
Original Topic: {topic}
Idea Concept: {idea_concept}
Detailed Plan: {idea_text}

**User Info**:
{user_context}
{user_behavior}

**Scoring Dimensions** (out of 10, with weights):
1. Topic Relevance (30%): Alignment and fit with the original topic
2. User Fit (20%): Match to user background, interests, and historical behavior
3. Feasibility (25%): Practical operability, resource reasonableness, implementation difficulty
4. Originality (25%): Uniqueness, novelty, and breakthrough thinking

**Scoring Requirements**:
- Pay special attention to User Fit; leverage the user's interests and behavior.
- If the idea fits the user's interests very well, give a high User Fit score.
- If user info is limited, score based on general usefulness and applicability.

Compute the weighted average final score out of 10.

Output format (strict):
Score: X.X
Reason: [Briefly explain the scores per dimension, especially User Fit.]"""

            score_response = ""
            try:
                score_response = self.model3.generate_text(prompt3, temperature=0.3)
                score = self._extract_score_from_response(score_response)
            except Exception as e:
                print(f"Scoring failed: {e}")
                score = 0.0
            
            # Filter by threshold
            if score >= Config.MIN_SCORE_THRESHOLD:
                filtered_ideas.append({
                    "idea": item["idea"],
                    "detail": item["detail"],
                    "model_score": score,
                    "evaluation_detail": score_response
                })
        
        # 5. Sort by model score (Gemini already considers personalization)
        result_ideas = sorted(filtered_ideas, key=lambda x: x.get("model_score", 0), reverse=True)
        
        # Return top-N ideas
        final_results = result_ideas[:num_ideas]
        
        # Update user interaction history if user_id provided
        if user_id and final_results:
            selected_ideas = [item["idea"] for item in final_results]
            try:
                self.user_profile.update_user_interaction(user_id, topic, selected_ideas)
            except Exception as e:
                print(f"Failed to update user interaction history: {e}")
        
        return final_results
    
    def _parse_ideas_from_output(self, output: str) -> List[str]:
        """Parse a list of ideas from the model's output."""
        ideas = []
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbering formats: "1. xxx", "1) xxx", "1、xxx"
            match = re.match(r'^\d+[.、)]\s*(.+)', line)
            if match:
                idea = match.group(1).strip()
                if len(idea) > 5:  # filter overly short lines
                    ideas.append(idea)
        
        return ideas
    
    def _extract_score_from_response(self, response: str) -> float:
        """Extract a numeric score from the evaluation response.

        Supports multiple formats:
        - English: "Score: 8.7", "Score 8.7", "8.7/10", "8.7 points"
        - Chinese (backward compatibility): "评分：8.7分", "8.7分"
        """
        # English patterns
        m = re.search(r'Score[:\s]+(\d+(?:\.\d+)?)', response, flags=re.IGNORECASE)
        if m:
            return float(m.group(1))
        m = re.search(r'(\d+(?:\.\d+)?)/10', response)
        if m:
            return float(m.group(1))
        m = re.search(r'(\d+(?:\.\d+)?)\s*points?', response, flags=re.IGNORECASE)
        if m:
            return float(m.group(1))

        # Chinese patterns (compatibility)
        m = re.search(r'评分[:：]?\s*(\d+(?:\.\d+)?)', response)
        if m:
            return float(m.group(1))
        m = re.search(r'(\d+(?:\.\d+)?)分', response)
        if m:
            return float(m.group(1))

        # Fallback: any number in text
        m = re.search(r'(\d+(?:\.\d+)?)', response)
        if m:
            score = float(m.group(1))
            if score > 10:  # maybe percentage
                score = score / 10.0
            return min(score, 10.0)
        
        return 0.0
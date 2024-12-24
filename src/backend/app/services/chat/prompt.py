from typing import Dict

CHAT_RECAP_PROMPT_TEMPLATE = """Analyze the provided conversation history and generate a structured summary focusing on the key details below. Ensure the summary is concise, clear, and avoids redundancy. Return the output in JSON format with the specified structure.

Conversation History:
{conversation_history}

Generate a structured summary that captures:

1. Context of the Issue
   - What prompted the client to initiate the conversation
   - Any explicit requests or expectations stated by the client

2. Conversation Highlights
   - Key exchanges in chronological order
   - Troubleshooting steps or significant discussion points

3. Participants and Roles
   - Who participated (client, bot, agents)
   - Their roles and contributions

4. Client Sentiment
   - Client's mood throughout the conversation

5. Communication Notes
   - Communication preferences or notable patterns

6. Unresolved Points
   - Unanswered questions or concerns
   - Issues lacking clarity

7. Important Agreements or Promises
   - Commitments or guarantees made
   - Deadlines or specific actions agreed upon

CLIENT_SENTIMENT_LIST: 
    # Positive Sentiments
    SATISFIED = "satisfied"           # Happy with the resolution/service
    GRATEFUL = "grateful"            # Expressing thanks and appreciation
    COOPERATIVE = "cooperative"      # Willing to follow instructions/help
    RELIEVED = "relieved"           # Problem has been resolved
    
    # Neutral Sentiments
    NEUTRAL = "neutral"             # Neither positive nor negative
    PROFESSIONAL = "professional"    # Formal, business-like tone
    INQUISITIVE = "inquisitive"     # Asking questions to understand better
    PATIENT = "patient"             # Willing to wait for resolution
    
    # Negative Sentiments
    FRUSTRATED = "frustrated"        # Difficulties with the situation
    ANGRY = "angry"                 # Strong negative emotions
    DISAPPOINTED = "disappointed"    # Expectations not met
    CONFUSED = "confused"           # Not understanding the process/solution
    
    # Time-Sensitive Sentiments
    URGENT = "urgent"               # Requires immediate attention
    ANXIOUS = "anxious"             # Worried about time/outcome
    IMPATIENT = "impatient"         # Wanting faster resolution
    
    # Specific Situation Sentiments
    SKEPTICAL = "skeptical"         # Doubtful about solution/process
    DEMANDING = "demanding"         # Insisting on specific outcomes
    APOLOGETIC = "apologetic"       # Sorry for confusion/mistakes
    CONCERNED = "concerned"         # Worried about implications
    OVERWHELMED = "overwhelmed"     # Finding process/situation too complex

Return the analysis in the following JSON structure (ensure valid JSON format):
{{
    "context_of_issue": "Brief description of what initiated the conversation and the client's explicit expectations.",
    "conversation_highlights": [
        "Key event or message 1",
        "Key event or message 2"
    ],
    "participants_and_roles": [
        {{
            "name": "Name",
            "role": "Role (Client/Agent/Bot)",
            "contribution": "Brief summary of their participation"
        }}
    ],
    "client_sentiment": "Sentiment of the client expressed as any one of the CLIENT_SENTIMENT_LIST",
    "communication_notes": "Any notable communication preferences or patterns",
    "unresolved_points": [
        "Unresolved point or question 1",
        "Unresolved point or question 2"
    ],
    "important_agreements_or_promises": [
        {{
            "promise": "Description of the commitment",
            "details": "Additional context, deadlines, or actions"
        }}
    ]
}}

Remember to:
- Maintain chronological order in conversation highlights
- Be specific about participant roles and contributions
- Include all attachments mentioned in the conversation
- Clearly state any deadlines or follow-up actions
- Preserve important technical details or reference numbers
"""

SYSTEM_PROMPT = """You are an AI assistant trained to analyze chat conversations and generate structured summaries. Your responses should be clear, accurate, and always in valid JSON format."""


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

4. Client Sentiment and Communication Notes
   - Client's mood throughout the conversation
   - Communication preferences or notable patterns

5. Unresolved Points
   - Unanswered questions or concerns
   - Issues lacking clarity

6. Attachments and Evidence
   - References to shared files, screenshots, or logs
   - Relevant external links or documents

7. Important Agreements or Promises
   - Commitments or guarantees made
   - Deadlines or specific actions agreed upon

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
    "client_sentiment_and_communication_notes": {{
        "sentiment": "Overall sentiment (e.g., frustrated, cooperative, calm)",
        "communication_notes": "Notable communication preferences or patterns"
    }},
    "unresolved_points": [
        "Unresolved point or question 1",
        "Unresolved point or question 2"
    ],
    "attachments_and_evidence": [
        {{
            "type": "Type of attachment (Screenshot/Log/File/Link)",
            "description": "Description of the attachment or reference"
        }}
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


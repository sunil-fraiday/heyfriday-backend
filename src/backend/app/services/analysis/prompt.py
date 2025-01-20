import json
from typing import Dict, List

few_shot_prompts = [
    {
        "current_message": "Can you provide the sales data for last year?",
        "chat_history": [
            "User: Hello, can I get some data?",
            "Assistant: Sure! What kind of data do you need?",
        ],
        "expected_output": {
            "Resource": "SalesData",
            "Scopes": ["query"],
        },
    },
    {
        "current_message": "What are the tickets raised for IT support?",
        "chat_history": [
            "User: I need help with an issue.",
            "Assistant: What specific issue are you referring to?",
        ],
        "expected_output": {
            "Resource": "ITSupport",
            "Scopes": ["query"],
        },
    },
    {
        "current_message": "Can you help me understand the revenue trends for this quarter?",
        "chat_history": [
            "User: Hi, I want some information on revenue.",
            "Assistant: Sure, what details about revenue would you like?",
            "User: I’m specifically interested in this quarter's trends.",
            "Assistant: Okay, are you looking for comparisons with previous quarters?",
        ],
        "expected_output": {
            "Resource": "RevenueData",
            "Scopes": ["query"],
        },
    },
    {
        "current_message": "How many tickets were resolved last week in IT support?",
        "chat_history": [
            "User: I’m curious about IT support details.",
            "Assistant: Could you clarify the specific details you need?",
            "User: I want to know about resolved tickets specifically.",
            "Assistant: Alright, resolved tickets for last week. Got it.",
        ],
        "expected_output": {
            "Resource": "ITSupport",
            "Scopes": ["query"],
        },
    },
]

INTENT_CLASSIFICATION_PROMPT_TEMPLATE = """
        Given the current message and chat history, classify the intent and map it to a resource and scope.
        Use the following resource mapping:
        {resource_mapping}
        
        Examples:
        {examples}

        Current Message: {current_message}
        Chat History: {chat_history}

        Give the result in the format of JSON and dont include anyother text.
        The JSON should be in the format of:
        {{
            "Resource": "The Resource that is needed to satisfy the current message asked by the user within the context",
            "Scopes": "The List of Scopes that is needed to be performed on the resource."
        }}
        """

category_few_shot_examples = [
    # General Inquiry - Policy
    {
        "current_message": "What's the process for requesting additional monitors? Do I need manager approval?",
        "chat_history": [],
        "expected_output": {
            "category": "general_inquiry",
            "proceed": True,
            "key_details": "User requesting information about hardware request process and approval requirements",
            "reasoning": "This is a policy-related inquiry that can be handled directly with documented information about hardware request procedures."
        }
    },

    # General Troubleshooting - Early Stage
    {
        "current_message": "Can't connect to the VPN from home. Getting 'Connection Failed' error.",
        "chat_history": [],
        "expected_output": {
            "category": "general_troubleshooting",
            "proceed": True,
            "key_details": "User experiencing VPN connection failure from home network",
            "reasoning": "Common VPN issue that starts with basic troubleshooting. Proceeding to verify basic connectivity and VPN client settings."
        }
    },

    # General Troubleshooting - Advanced Stage
    {
        "current_message": "Still can't connect. Internet is working fine, VPN client is updated, and I've restarted.",
        "chat_history": [
            "Is your internet connection working?",
            "Yes, can browse websites fine",
            "Please try updating the VPN client",
            "Done, still same issue",
            "Let's try restarting your computer",
            "Just did, no change"
        ],
        "expected_output": {
            "category": "general_troubleshooting",
            "proceed": False,
            "key_details": "Persistent VPN connection failure. Confirmed: internet working, client updated, restart attempted. Basic troubleshooting exhausted",
            "reasoning": "While started as general troubleshooting, basic steps haven't resolved the issue. Comprehensive troubleshooting history gathered, now requires network team investigation."
        }
    },

    # Technical Troubleshooting - Initial Assessment
    {
        "current_message": "Excel keeps crashing when I try to open files containing macros. Already tried repair and reinstall.",
        "chat_history": [],
        "expected_output": {
            "category": "technical_troubleshooting",
            "proceed": True,
            "key_details": "Excel crashing specifically with macro files. User has attempted repair and reinstall",
            "reasoning": "Complex application issue but proceeding to gather specific error messages and verify macro security settings before specialist handoff."
        }
    },

    # Software Installation - Initial Request
    {
        "current_message": "Need to install Python and some data science packages for a new project.",
        "chat_history": [],
        "expected_output": {
            "category": "software_installation",
            "proceed": False,
            "key_details": "User requesting Python installation with data science packages for project work",
            "reasoning": "While software installation category, proceeding to gather specific package requirements and verify if they're pre-approved for installation."
        }
    },

    # Hardware Equipment - Assessment
    {
        "current_message": "My laptop battery only lasts 30 minutes now. It's only 6 months old.",
        "chat_history": [],
        "expected_output": {
            "category": "hardware_equipment_order",
            "proceed": True,
            "key_details": "Laptop battery degradation issue, 6-month-old device with 30-minute battery life",
            "reasoning": "Though hardware issue, proceeding to gather usage patterns and run battery diagnostics before replacement request."
        }
    },

    # Password Reset - Simple
    {
        "current_message": "Need to reset my Windows password, it expired this morning.",
        "chat_history": [],
        "expected_output": {
            "category": "password_reset",
            "proceed": False,
            "key_details": "Standard Windows password reset request due to expiration",
            "reasoning": "Basic password reset request. Proceeding to verify user identity and guide through self-service reset if available."
        }
    },

    # Access Management - Initial Request
    {
        "current_message": "Need access to the marketing team's SharePoint site. I just joined the team.",
        "chat_history": [],
        "expected_output": {
            "category": "access_management",
            "proceed": True,
            "key_details": "New team member requesting SharePoint access for marketing team site",
            "reasoning": "Access request needs verification but proceeding to gather manager details and specific access requirements."
        }
    },

    # Network Issues - Complex
    {
        "current_message": "Getting really slow internet speeds on the 3rd floor, but 2nd floor is fine.",
        "chat_history": [],
        "expected_output": {
            "category": "network_issues",
            "proceed": True,
            "key_details": "Location-specific network performance issue, limited to 3rd floor",
            "reasoning": "While network infrastructure issue, proceeding to gather affected user count, specific times, and speed test results for network team."
        }
    },

    # Security Issues - Initial Report
    {
        "current_message": "I think I clicked on a suspicious link in an email. My antivirus is showing warnings.",
        "chat_history": [],
        "expected_output": {
            "category": "security_issues",
            "proceed": True,
            "key_details": "Potential security incident: suspicious link clicked, antivirus warnings active",
            "reasoning": "Security issue but proceeding to gather essential details: email source, warning messages, and any system changes noticed."
        }
    },

    # Onboarding - System Setup
    {
        "current_message": "Starting next week, need my laptop and system access set up.",
        "chat_history": [],
        "expected_output": {
            "category": "onboarding",
            "proceed": True,
            "key_details": "New employee requesting initial system setup and access",
            "reasoning": "Standard onboarding request. Proceeding to verify employment details and gather specific access requirements."
        }
    },

    # Offboarding - Account Closure
    {
        "current_message": "Need to terminate system access for John Smith, his last day was yesterday.",
        "chat_history": [],
        "expected_output": {
            "category": "offboarding",
            "proceed": False,
            "key_details": "Access termination request for departed employee John Smith",
            "reasoning": "Already have enough information regarding John Smith's termination. Proceeding to initiate account closure process."
        }
    }
]


CATEGORISE_CONVERSATION_PROMPT_TEMPLATE = """
You are an expert IT support ticket analyzer and assistant. You work alongside specialized systems and human agents to provide comprehensive support. Your role is to:
1. Analyze and categorize support requests
2. Assist with information gathering and initial debugging for ALL issues
3. Handle general inquiries and basic troubleshooting directly
4. Ensure smooth transitions to specialist teams when needed

Available categories:
- general_inquiry (Basic information requests about policies, services, etc.)
- general_troubleshooting (Common problems solvable with basic steps)
- technical_troubleshooting (Complex issues needing deep technical knowledge)
- software_installation
- hardware_equipment_order
- password_reset
- offboarding
- onboarding
- access_management
- network_issues
- security_issues
- other

System Capabilities and Approach:
- The automated response system can fully handle:
  * general_inquiry: Basic information requests, policy questions, service details
  * general_troubleshooting: Common issues with documented solutions

- For ALL other categories, you should:
  * Gather relevant diagnostic information but dont exceed many followup questions and handover after max 2 followup questions
  * Guide through safe preliminary troubleshooting steps
  * Document attempted solutions and their outcomes
  * Help narrow down the root cause
  * Only transition to specialists after gathering useful context

Progressive Assistance Guidelines:
1. Initial Response (Always proceed=true):
   * Acknowledge the issue
   * Ask clarifying questions
   * Request relevant details
   * Suggest safe diagnostic steps

2. Follow-up Assistance (proceed=true if):
   * Still gathering important information but after 2 followup questions handover to specialist
   * User is following troubleshooting steps
   * Current steps might resolve the issue

3. Specialist Transition (proceed=false when):
   * Sufficient information gathered to confirm specialist need
   * Issue confirmed to require elevated access
   * Good clear security or compliance implications
   * Technical intervention needed

Format your response as a JSON object:
{{
    "category": "category_name",
    "proceed": boolean,
    "key_details": "Description of the issue, gathered information, and troubleshooting steps",
    "reasoning": "Explanation of category and current decision to proceed or transition",
}}
1
Examples:
{examples}

CurrentMessage:
{current_message}

ConversationHistory:
{chat_history}
"""

def get_formatted_few_shot_prompts(few_shot_prompts: List[Dict]):
    example_strings = []
    for example in few_shot_prompts:
        example_str = f"""
        Current Message: {example['current_message']}
        Chat History: {' | '.join(example['chat_history'])}
        Expected Output: {json.dumps(example['expected_output'], indent=4)}
        """
        example_strings.append(example_str)
    return example_strings


# def get_final_few_shot_prompt(chat_history, resource_mapping):
#     examples_combined = "\n".join(get_formatted_few_shot_prompts())
#     formatted_prompt = prompt_template.format(
#         resource_mapping=resource_mapping,
#         examples=examples_combined,
#         current_message="Can you fetch the revenue details for Q3?",
#         chat_history="\n".join(chat_history),
#     )
#     return formatted_prompt

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
    {
        "current_message": "Hi IT team, I need a new monitor for my desk as my current one is too small for my work. Can you help me order one?",
        "chat_history": [],
        "expected_output": {
            "category": "hardware_equipment_order",
            "key_details": "Employee requesting new monitor for workspace",
            "reasoning": "The request is specifically for ordering hardware equipment (monitor) for workplace use",
        },
    },
    {
        "current_message": "Can't access Slack after joining the team today. Getting an error about account not being set up.",
        "chat_history": [
            "Welcome to the team! Let me help you with Slack access.",
            "Thank you! Yes, I'm trying to log in but getting access denied.",
        ],
        "expected_output": {
            "category": "access_management",
            "key_details": "New employee unable to access Slack, account setup required",
            "reasoning": "This involves managing access to a corporate application (Slack) for a new team member",
        },
    },
    {
        "current_message": "My laptop keeps disconnecting from the office WiFi every few minutes. It's affecting my work.",
        "chat_history": [
            "Have you tried restarting your laptop?",
            "Yes, I did that twice but still having the same issue.",
        ],
        "expected_output": {
            "category": "network_issues",
            "key_details": "Intermittent WiFi connectivity issues with laptop",
            "reasoning": "The issue involves network connectivity problems specifically related to WiFi connection stability",
        },
    },
    {
        "current_message": "Hi, I need to reset my password for my Windows login. It's expired and I can't get in.",
        "chat_history": [],
        "expected_output": {
            "category": "password_reset",
            "key_details": "User requesting Windows login password reset due to expiration",
            "reasoning": "Direct request for password reset assistance for a system account",
        },
    },
    {
        "current_message": "I'm trying to install the new version of Adobe Creative Suite but getting an error code 150.",
        "chat_history": [
            "What error message are you seeing exactly?",
            "It says 'Error 150: Installation failed due to insufficient permissions'",
        ],
        "expected_output": {
            "category": "software_installation",
            "key_details": "Adobe Creative Suite installation failing with error 150, permission issues",
            "reasoning": "The conversation involves troubleshooting software installation problems with specific error codes",
        },
    },
    {
        "current_message": "My Outlook keeps crashing when I try to open attachments. I've tried restarting but it's still happening.",
        "chat_history": [],
        "expected_output": {
            "category": "technical_troubleshooting",
            "key_details": "Outlook application crashing specifically when handling attachments",
            "reasoning": "This requires specific technical troubleshooting as it involves application behavior with particular conditions",
        },
    },
    {
        "current_message": "What are the working hours for the IT helpdesk? I might need support over the weekend.",
        "chat_history": [],
        "expected_output": {
            "category": "general_inquiry",
            "key_details": "User asking about IT helpdesk operating hours and weekend availability",
            "reasoning": "This is a simple information request about service availability, not requiring any technical support or troubleshooting",
        },
    },
    {
        "current_message": "Hi, where can I find the company's policy on bringing personal devices to work? I'd like to use my own laptop sometimes.",
        "chat_history": [],
        "expected_output": {
            "category": "general_inquiry",
            "key_details": "Employee requesting information about BYOD (Bring Your Own Device) policy",
            "reasoning": "This is an informational query about company IT policies without any technical issues to resolve",
        },
    },
    {
        "current_message": "My microphone isn't working in Microsoft Teams. The icon shows it's on but nobody can hear me.",
        "chat_history": ["Have you checked if it's selected as the default device?", "Where do I check that?"],
        "expected_output": {
            "category": "general_troubleshooting",
            "key_details": "User experiencing microphone issues in Teams meetings, needs help with audio settings",
            "reasoning": "This is a common audio configuration issue that can be resolved with basic troubleshooting steps like checking device settings",
        },
    },
    {
        "current_message": "The printer on the second floor isn't showing up in my list of printers anymore. I was able to print yesterday.",
        "chat_history": [],
        "expected_output": {
            "category": "general_troubleshooting",
            "key_details": "User unable to see network printer in printer list, previously working",
            "reasoning": "This is a common printer connectivity issue that typically can be resolved with basic steps like checking network connection or refreshing printer list",
        },
    },
    {
        "current_message": "I accidentally deleted some files from my OneDrive. Is there a way to get them back?",
        "chat_history": ["When did you delete them?", "About an hour ago"],
        "expected_output": {
            "category": "general_troubleshooting",
            "key_details": "User needs help recovering recently deleted files from OneDrive",
            "reasoning": "This is a standard file recovery scenario that can be resolved using built-in OneDrive recovery features, requiring only basic guidance",
        },
    },
]


CATEGORISE_CONVERSATION_PROMPT_TEMPLATE = """
You are an expert IT support ticket analyzer. Given the following CurrentMessage and ConversationHistory from a support ticket, please:
1. Identify the category of the conversation from these options:
   - general_inquiry
   - general_troubleshooting (Troubleshooting very common problems that can be dealt by straightforward troubleshooting)
   - technical_troubleshooting (Troubleshooting very specific problems that require a deeper understanding of the system or user intervention to troubleshoot)
   - software_installation
   - hardware_equipment_order
   - password_reset
   - offboarding
   - onboarding
   - access_management
   - network_issues
   - security_issues
   - other (If none of the above categories apply)

2. Extract key details about the request. 
3. Reason on why you assinged this category to this conversation. 

Examples:
{examples}

Format your response as a JSON object with the following structure:
{{
    "category": "category_name",
    "key_details": "Brief description of the key points",
    "reasoning": "Brief explanation of how you arrived at the conclusion"
}}

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

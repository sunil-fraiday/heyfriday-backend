import json

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


def get_formatted_few_shot_prompts():
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

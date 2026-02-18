import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_draft(topic: str, model: str = "gpt-5-mini") -> str:
    """
    uses a language model to generate a complete draft essay
    """

    ### START OMIT BLOCK
    prompt = f"""
    Write a well-structured draft essay in response to the following topic.
    The draft should include an introduction, body, and conclusion.

    topic:
    {topic}
    """

    # Get a response from the LLM by creating a chat with the client.
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return response.choices[0].message.content


def reflect_on_draft(draft: str, model: str = "gpt-5-mini") -> str:
    """
    uses a language model to provide constructive feedback on the essay draft
    """
    prompt = f"""
    Analyze the essay draft and provide a constructive feedback.
    Point out the areas of improvements and suggestions.
    Draft:
    {draft}
    """

    # Get a response from the LLM by creating a chat with the client.
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return response.choices[0].message.content


def revise_draft(original_draft: str, reflection: str, model: str = "gpt-5-mini") -> str:
    """
    improves a given essay draft based on feedback from a reflection step
    """
    prompt = f"""
    Revise the essay draft based on the reflection provided.
    Improve it in terms of clarity and coherence and provide the final essay.
    
    Draft:
    {original_draft}
    
    Reflection:
    {reflection}
    """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
    )

    return response.choices[0].message.content


def main():
    essay_prompt = "Should social media platforms be regulated by the government?"

    # Agent 1 – Draft
    draft = generate_draft(essay_prompt)
    print("📝 Draft:\n")
    print(draft)

    # Agent 2 – Reflection
    feedback = reflect_on_draft(draft)
    print("\n🧠 Feedback:\n")
    print(feedback)

    # Agent 3 – Revision
    revised = revise_draft(draft, feedback)
    print("\n✍️ Revised:\n")
    print(revised)

if __name__ == "__main__":
    main()



import os
import logging
from typing import List, Dict
from pydantic import BaseModel, Field

from openai import OpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5-nano"


# Data Models
class SubTask(BaseModel):
    section_type: str = Field("Type of blog's section to write")
    description: str = Field("Quick description of the what should cover")
    style_guide: str = Field("Writing style for the section")
    target_length: int = Field("Target word count for this section")

class OrchestratorPlan(BaseModel):
    """Plan for blog structure and sub-tasks"""
    topic_analysis: str = Field("Analysis of the blog topic")
    target_audience: str = Field("Potential audience for the blog")
    sections: list[SubTask] = Field("List of sections to write")

class SectionContent(BaseModel):
    """Section content for blog writing"""
    content: str = Field("Written content for the section")
    key_points: list[str] = Field("Main points covered by the section")

class SuggestedEdits(BaseModel):
    """Suggested edits for a section"""
    section_name: str = Field(description="Name of the section")
    suggested_edit: str = Field(description="Suggested edit")

class ReviewFeedback(BaseModel):
    """Final review and suggestions"""
    cohesion_score: float = Field(description="How well sections flow together (cohesion score between 0 and 1)")
    suggested_edits: List[SuggestedEdits] = Field(
        description="Suggested edits by section"
    )
    final_version: str = Field(description="Complete, polished blog post")

class BlogPost(BaseModel):
    """Blog post"""
    structure: OrchestratorPlan = Field("Planned structure of the blog")
    sections: Dict[str, SectionContent] = Field("Section content")
    review: ReviewFeedback =  Field("Feedback review for improvement suggestions.")

# Prompts
ORCHESTRATOR_PROMPT = """
Analyze this blog topic and break it down into logical sections.

Topic: {topic}
Target Length: {target_length} words
Style: {style}

Return your response in this format:

# Analysis
Analyze the topic and explain how it should be structured.
Consider the narrative flow and how sections will work together.

# Target Audience
Define the target audience and their interests/needs.

# Sections
## Section 1
- Type: section_type
- Description: what this section should cover
- Style: writing style guidelines

[Additional sections as needed...]
"""

WORKER_PROMPT = """
Write a blog section based on:
Topic: {topic}
Section Type: {section_type}
Section Goal: {description}
Style Guide: {style_guide}
Note: {previous_sections}

Return your response in this format:

# Content
[Your section content here, following the style guide]

# Key Points
- Main point 1
- Main point 2
[Additional points as needed...]
"""

REVIEWER_PROMPT = """
Review this blog post for cohesion and flow:

Topic: {topic}
Target Audience: {audience}

Sections:
{sections}

Provide a cohesion score between 0.0 and 1.0, suggested edits for each section if needed, and a final polished version of the complete post.

The cohesion score should reflect how well the sections flow together, with 1.0 being perfect cohesion.
For suggested edits, focus on improving transitions and maintaining consistent tone across sections.
The final version should incorporate your suggested improvements into a polished, cohesive blog post.
"""

class BlogOrchestrator:
    def __init__(self):
        self.sections_content = {}

    # Routing Functions
    def get_orchestrator_plan(self, topic_name: str, target_length: int, writing_style: str) -> OrchestratorPlan:
        """Retrieves the plan for blog writing"""

        completion = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": ORCHESTRATOR_PROMPT.format(topic=topic_name,
                                                          target_length=target_length,
                                                          style=writing_style),
                }
            ],
            response_format=OrchestratorPlan
        )

        plan = completion.choices[0].message.parsed

        return plan


    def write_section(self, topic_name: str, section: SubTask) -> SectionContent:
        """Writes a specific blog section with previous section context"""

        previous_sections = "\n".join(
            [
                f"=== {section_type} ===\n{content.content}"
                for section_type, content in self.sections_content.items()
            ]
        )

        completion = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": WORKER_PROMPT.format(topic=topic_name,
                                                    section_type=section.section_type,
                                                    description=section.description,
                                                    style_guide=section.style_guide,
                                                    previous_sections=f"Previous sections:{previous_sections}" if previous_sections else "This is the first section."
                                                    ),
                }
            ],
            response_format=SectionContent
        )

        section_content = completion.choices[0].message.parsed

        return section_content


    def review_blog_post(self, topic_name: str, plan: OrchestratorPlan) -> ReviewFeedback:
        """Analyzes and improve the overall blog cohesion and flow"""
        sections_text = "\n\n".join(
            [
                f"##{section_type}\n{section_content.content}" for
                section_type, section_content in self.sections_content.items()
            ]
        )

        completion = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": REVIEWER_PROMPT.format(topic=topic_name,
                                                      audience=plan.target_audience,
                                                      sections=sections_text
                                                    ),
                }
            ],
            response_format=ReviewFeedback
        )

        review = completion.choices[0].message.parsed

        return review


    def write_blog(self, topic_name: str, target_length: int= 1000, writing_style: str="informative") -> BlogPost:
        """Processes the entire blog writing task"""
        logging.info(f"Starting blog writing for topic '{topic_name}'...")

        logging.info(f"Planning blog structure")
        plan = self.get_orchestrator_plan(topic_name, target_length, writing_style)
        logging.info(f"Plan processed.")

        # print(plan.model_dump())

        logging.info("Writing sections...")
        for section in plan.sections:
            logging.info(f"Writing '{section.section_type}' section")
            section_content = self.write_section(topic_name, section)
            self.sections_content[section.section_type] = section_content

        logging.info(f"Blog writing complete.")

        logging.info("Reviewing full blog post")
        review = self.review_blog_post(topic_name, plan)

        logging.info("Process complete.")

        return BlogPost(
            structure=plan,
            sections=self.sections_content,
            review=review
        )



if __name__ == "__main__":
    blog_writer = BlogOrchestrator()

    topic = "The impact of AI on software development"
    blog = blog_writer.write_blog(
        topic_name=topic,
        target_length=1200,
        writing_style="informative"
    )

    print(f"Final Blog Post: \n{blog.review.final_version}")
    print(f"Cohesion score: {blog.review.cohesion_score}")

    suggested_edits = blog.review.suggested_edits
    if suggested_edits:
        for edit in suggested_edits:
            print(f"Section: {edit.section_name}")
            print(f"Suggestions: {edit.suggested_edit}")
    else:
        print("No suggested edits")










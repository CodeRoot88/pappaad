import re
from typing import Annotated, List

import instructor
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import AfterValidator, BaseModel
from app.recommendations.new_keywords.keyword_prompts import (
    derive_theme_representation,
    evaluate_keyword_fitness_to_theme,
)

_ = load_dotenv()


class SiteLinksForAds(BaseModel):
    urls: list[str]


class AdKeywordsHeadlinesDescriptions(BaseModel):
    keywords: List[str]
    headlines: List[dict[Annotated[str, str], str]]
    descriptions: List[str]


CLIENT = instructor.from_openai(OpenAI())


def get_recommended_urls_for_ads(links: list[str], num: int = 5) -> SiteLinksForAds:
    worthy_links = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=SiteLinksForAds,
        messages=[
            {
                "role": "system",
                "content": "You're a expert marketing consultant for a client who wants to run Google ads for their website.",
            },
            {
                "role": "user",
                "content": f"""
                Below are the links for my site. I need you to choose the best {num} links to run google ads, home page must be included. {links}
                Include product lists, services, and other important pages.
                Do not include about us, contact us, pricing, privacy policy or other non-essential pages
                """,
            },
        ],
    )
    return worthy_links


class TCPAEXtractionData(BaseModel):
    tcpa: int
    summary: str


def gen_tcpa(content: str, currency: str) -> TCPAEXtractionData:
    tcpa = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=TCPAEXtractionData,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                       TCPA Extraction Prompt for Website Summaries
You are an AI assistant specialized in extracting key financial metrics from website summaries. You analyze websites to determine the Target Cost Per Acquisition (TCPA) for Google Ad Campaigns.

Your task is to analyze the given website summary and extract the TCPA or the minimum cost mentioned for services. Use the specified currency parameter for all financial information, formatting it as follows:
- For USD, use `$ 5000`
- For EUR, use `€ 5000`
- For other currencies, follow the same pattern with the currency symbol followed by a space and the amount.

Follow these steps:
1. Carefully read through the entire website summary.
2. Look for any mentions of pricing, cost, or financial information.
3. Identify the lowest or starting price point mentioned for services.
4. Determine the vertical. Assess the typical lifetime value (LTV) of a customer.
5. Determine the business model, average cost of a customer, and likelihood of converting.
6. Use explicit pricing and the provided currency parameter to calculate a TCPA based on the LTV and propensity to purchase.

Report your findings in the following format:
[TCPA in specified currency]
Example output:
 TCPA: $ 800
 Summary: Glitch is an AI-powered platform that automates Google Ads management for high-growth businesses. While explicit pricing isn't provided, the SaaS model likely includes tiered subscriptions based on ad spend. With a typical customer lifetime value (LTV) of around $ 50,000 and an estimated customer acquisition cost (CAC) of $ 2,000, the target cost per acquisition (TCPA) is approximately $ 400, assuming a 20% conversion rate.

Example input:
Title: Home | Glitch
URL Source: http://glitchads.ai/
Markdown Content:
![Image 1](https://static.wixstatic.com/media/3cce5b_3a2136c504dd4108a63eaf9a0547025c~mv2.png/v1/fill/w_64,h_40,al_c,q_85,usm_0.66_1.00_0.01,enc_auto/3cce5b_3a2136c504dd4108a63eaf9a0547025c~mv2.png)
Supercharging
--------------
 Online Growth
For Scaling Companies
---------------------------------------
Supercharge your online growth with AI optimisation for as little as € 100.
Join Waiting List
-----------------
Get early access and become a Glitch beta tester today!
What We Offer
-------------
### Leveraging Data to Supercharge Growth
At Glitch, our main focus is removing the insights gap that exists between marketing and sales. By leveraging the rich campaign data and integrating it back into the sales pipeline, our users can supercharge growth like never before.
### AI-Powered Optimisation

Our AI-powered solutions ensure that your campaigns are dynamic and targeted to the right audience. We use the latest AI technologies and automation to optimise campaigns.
### Actionable Performance Updates
We believe that data is the key to success in online growth. Our AI enables you to make informed decisions to improve results within seconds. This data is seamlessly shared back into your sales pipeline to reduce silos between marketing and sales.
###  99% Faster
We make it easy to grow your customer base using online campaigns, no matter what your budget or expertise. Using AI and automation we streamline the process, so you can start acquiring customers 99% quicker than doing it yourself.
-----
New Input:
            {content}
            Currency: {currency}
            """,
            },
        ],
    )

    return tcpa


def llm_output_constraint_check(v: str, length: int = 30) -> str:
    """
    Check if the output is less than the specified length and does not contain any punctuation or special characters.
    """
    if len(v) > length:
        raise ValueError(f"Text must be less than {length} characters")

    pattern = re.compile(r"^[a-zA-Z0-9 ]*$")
    if not pattern.match(v):
        return re.sub(r"[^\w\s]", "", v)

    return v


class AdKeywordsHeadlines(BaseModel):
    keywords: List[str]
    headlines: List[dict[Annotated[str, str], str]]


class CampaignBusinessDescription(BaseModel):
    business_desc: str


def regenerate_headline(content, headline):
    if len(headline["headline"]) <= 29:
        return headline
    if len(headline["headline"]) > 29:
        keyword = headline["keyword"]
        try:
            new_headline_result = gen_ad_keyword_headline(content, keyword)
            new_headline = {"keyword": keyword, "headline": new_headline_result.headline}
            return new_headline
        except Exception as e:
            raise Exception(f"Failed to generate valid headline for this keyword {headline.keyword} {e}")


class AdGoalDescription(BaseModel):
    ad_goal: str


def gen_ad_theme(content: str, business_desc: str, keywords: list[str]) -> AdGoalDescription:
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=AdGoalDescription,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Create a theme for a Google ad based on the following page content, keywords and business description of the customer
                # Content:
                {content}
                # Business Description:
                {business_desc}
                # Keywords:
                {", ".join(keywords)}
                """,
            },
        ],
    )
    return result


class AdKeywordsDescriptions(BaseModel):
    descriptions: list[str]


def gen_ad_descriptions(content: str, keywords: list[str]) -> list[str]:
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=AdKeywordsDescriptions,
        max_retries=5,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Create 4 descriptions for a Google ad based on the following content and keywords.
                They should be 80 characters or less including blanks space.
                They should each contain one of the keywords.
                No emojis are allowed.
                # Content:
                {content}
                # Keyword:
                {keywords}
                """,
            },
        ],
    )
    return result.descriptions


def gen_business_description(content: str):
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=CampaignBusinessDescription,
        max_retries=5,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Create a business description based on the following content.
                # Content:
                {content}
                """,
            },
        ],
    )
    return result


class AdKeywordHeadline(BaseModel):
    keyword: str
    headline: str


class AdKeywordHeadlines(BaseModel):
    keyword: str
    headlines: list[str]


def gen_ad_keyword_headline(content: str, keyword: str, max_retries: int = 5, existing_headlines: list[str] = []):
    for _ in range(max_retries):
        result = CLIENT.chat.completions.create(
            model="gpt-4o",
            response_model=AdKeywordHeadlines,
            max_retries=max_retries,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert marketing consultant tasked with creating a Google ad for a client's website.",
                },
                {
                    "role": "user",
                    "content": f"""
                Begin by replacing any misspelled keyword or keyword that includes unnecessary spaces (i.e. 'he lp' instead of 'help').
                Use the correctly spelled keyword instead.

                It is crucially important that the headline reflects the content,

                Example:
                Content: We are a SAAS Gym Company
                Keyword: Gym
                Headline: Gym Software for Fitness Centers

                Content: We are a SAAS HomeCare Company
                Keyword: HomeCare Nurse
                Headline: HomeCare Nurse Management
                Please generate ten headlines for a Google ad based on the following guideline and provided content (in markdown format) and keyword:

                # Guideline:
                * Titleize each word in the headline.
                * The headline must include the keyword.
                * The headline must be 25 characters or fewer.
                * No punctuation or special characters are allowed.
                * No emojis are allowed.

                Please return the keyword and generated headlines

                # Content:
                {content}
                # Keyword:
                {keyword}
                """,
                },
            ],
        )
        # If headline contains the keyword, return the result
        for headline in result.headlines:
            if len(headline) <= 29 and headline not in existing_headlines:
                return AdKeywordHeadline(keyword=keyword, headline=headline)
            else:
                continue
    # If all retries fail, raise an exception
    raise Exception(f"Failed to generate a valid headline after {max_retries} retries")


class SiteLinkNameDescriptionsCallout(BaseModel):
    url: str
    name: Annotated[str, AfterValidator(lambda v: llm_output_constraint_check(v, 25))]
    description1: Annotated[str, AfterValidator(lambda v: llm_output_constraint_check(v, 35))]
    description2: Annotated[str, AfterValidator(lambda v: llm_output_constraint_check(v, 35))]
    callout: Annotated[str, AfterValidator(lambda v: llm_output_constraint_check(v, 25))]


def gen_sitelink_name_descriptions_and_callout(url: str, content: str):
    """
    Generate sitelink name and descriptions based on the provided content.
    """
    result = CLIENT.chat.completions.create(
        model="gpt-4o-mini",
        response_model=SiteLinkNameDescriptionsCallout,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
            Generate a name, two descriptions and one google ad callout for this site link {url} based provided content (in markdown format) and following the guidelines provided.

            # Guidelines:
            * name and callout must be 25 characters or fewer.
            * Descriptions must be 35 characters or fewer.
            * No punctuation or special characters are allowed.
            * No emojis are allowed.

            # Content:
            {content}
            """,
            },
        ],
    )

    return result


class ThemeRepresentation(BaseModel):
    theme: str


def get_theme_representation(contextual_info: str, keywords: list[str]) -> str:
    """Get a theme representation from a set of keywords using the LLM."""
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=ThemeRepresentation,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing strategist analyzing keyword themes.",
            },
            {
                "role": "user",
                "content": derive_theme_representation(contextual_info, keywords),
            },
        ],
    )
    return result.theme


class KeywordFitness(BaseModel):
    fitness_score: float


def evaluate_keyword_fitness(candidate_keyword: str, training_keywords: list[str], theme_representation: str) -> float:
    """Evaluate how well a candidate keyword fits with a given theme."""
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=KeywordFitness,
        messages=[
            {
                "role": "system",
                "content": "You are an expert in semantic analysis and keyword classification.",
            },
            {
                "role": "user",
                "content": evaluate_keyword_fitness_to_theme(
                    candidate_keyword, training_keywords, theme_representation
                ),
            },
        ],
    )
    return result.fitness_score


class GeneratedKeywords(BaseModel):
    keywords: list[str]


def generate_specific_keywords(content: str, keywords: list[str]) -> list[str]:
    """
    Generate specific keywords based on the provided content and keywords.
    """
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=GeneratedKeywords,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Generate more specific keywords based on the following content and keywords.
                Just return the keywords, no other text.
                # Content:
                {content}
                # Keywords:
                {keywords}
                """,
            },
        ],
    )
    return result.keywords


def generate_generic_keywords(content: str, keywords: list[str]) -> list[str]:
    """
    Generate generic keywords based on the provided content and keywords.
    """
    result = CLIENT.chat.completions.create(
        model="gpt-4o",
        response_model=GeneratedKeywords,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Generate more generic keywords based on the following content and keywords.
                Just return the keywords, no other text.
                # Content:
                {content}
                # Keywords:
                {keywords}
                """,
            },
        ],
    )
    return result.keywords


class CampaignName(BaseModel):
    name: str


def generate_campaign_name_from_content(content: str, location: str, type: str):
    result = CLIENT.chat.completions.create(
        model="gpt-4o-mini",
        response_model=CampaignName,
        messages=[
            {
                "role": "system",
                "content": "You are an expert marketing consultant tasked with creating Google ads for a client's website.",
            },
            {
                "role": "user",
                "content": f"""
                Create a name for a Google ad based on the following content.
                The name should be of the form
                Glitch |  Type | Location | One to Two word description of Content

                An example:

                Glitch | Prospecting | USA | AI Growth

                Use the following content to generate the name:
                # Content:
                {content}
                # Location:
                {location}
                # Type:
                {type}
                """,
            },
        ],
    )
    return result

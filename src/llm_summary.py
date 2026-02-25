"""LLM-based executive summary generation for decomposition results."""

import os
import pandas as pd
from openai import OpenAI, APIError, RateLimitError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Module-level client singleton — created once, reused across calls.
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    """Return the shared OpenAI client, initialising it on first call.

    Raises:
        ValueError: If OPENAI_API_KEY is not set.
    """
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )
    if _client is None:
        _client = OpenAI()
    return _client




def evaluate_executive_summary(summary: str) -> str:
    """Polish the executive summary for clarity and conciseness.

    Raises:
        ValueError: If OPENAI_API_KEY is not set or quota/rate limit is reached.
        APIError: If the OpenAI API call fails for another reason.
    """
    client = _get_client()

    prompt = f"""
You are an expert data analyst and executive communication coach.

TASK
Rewrite the executive summary below so it is clear, concise, and easy for an executive to read.
Improve wording and fix obvious grammar, spacing, and punctuation issues.
Do not change any numbers or the business meaning.

OUTPUT FORMAT (very important)
- Output plain text only.
- You may use:
  - section labels such as "A. Headline", "B. Driver attribution", etc.
  - line breaks
  - bullet points that start with "- "
- Do NOT use any other markdown or special formatting:
  - no headings with #
  - no bold or italics
  - do not output the characters *, _, `, ~, >, $, or backslashes
  - no LaTeX
  - no emojis
- Do not wrap the answer in quotes or a code block.
- Do not add any commentary before or after the summary.
- Start directly with the first section label (e.g. "A. Headline").

Executive summary draft:
{summary}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_executive_summary(
    metric_name: str,
    formula: str,
    outcome_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    numerators: list,
    denominators: list,
) -> str:
    """Generate an executive summary using the OpenAI API.

    Args:
        metric_name: Name of the metric being analyzed
        formula: Formula string for the metric
        outcome_df: DataFrame with outcome metric summary (single row, formatted)
        drivers_df: DataFrame with driver contributions (raw data with numeric values)
        numerators: List of numerator driver names (multipliers with positive correlation)
        denominators: List of denominator driver names (divisors with negative correlation)

    Returns:
        Generated executive summary text

    Raises:
        ValueError: If OpenAI API key is not found or quota/rate limit is reached.
        APIError: If the OpenAI API call fails for another reason.
    """
    client = _get_client()

    clean_metric_name = metric_name.split("_")[0]

    prompt = f"""
You are an LLM acting as an Expert Data Analyst. Your task is to generate a short, accurate, and formula-aligned summary of the period-over-period change in {clean_metric_name}.

Follow all instructions exactly. Do not add information not present in the inputs.

---

1. Metric Logic
You are analyzing the metric using the functional relationship:

Formula: {formula}

Classify drivers based on their position in the formula:

- Numerators (Direct Effect): Increasing these increases the metric.
Numerators: {', '.join(numerators) if numerators else 'None'}

- Denominators (Inverse Effect): Increasing these decreases the metric.
Denominators: {', '.join(denominators) if denominators else 'None'}

You must use this logic in every driver explanation.

---

2. Input Tables
A. Outcome Metric
{outcome_df.to_markdown(index=False)}

B. Driver Contributions
{drivers_df.to_markdown(index=False)}

---

3. Required Output Structure
Your summary must contain exactly three sections:

A. Headline (2 bullets)
- State the overall % and absolute change in {clean_metric_name}.
- Define the so what for an executive audience describing the drivers contributions.

B. Driver Attribution (3-6 sentences)
For each driver in the table:

1. State whether the driver was a Tailwind (+) or Headwind (-).
2. State the driver's own change (e.g., "Traffic increased 12%").
3. Explain its effect using formula logic:
- If numerator: "Because it is a numerator, this movement raised/lowered {clean_metric_name} by [Contribution]."
- If denominator: "Because it is a denominator, this movement put upward/downward pressure on {clean_metric_name} by [Contribution]."
4. Use the actual contribution value from the table.

Follow this sentence template where possible:
"[Driver] [increased/decreased] by X%, acting as a [Tailwind/Headwind]. Because it is a [numerator/denominator], this movement [increased/decreased] {clean_metric_name} by [Contribution]."

C. Primary Driver (1 sentence)
- Identify the driver with the largest absolute contribution.
- State whether it explains most of the total change.

D. Next Step Ideas
- Generate 2 to 3 next step ideas for further analysis based on the results and executive summary.

---

4. Style Requirements
- Format the output in plain text only.
- Be concise and deterministic.
- No speculation.
- No metaphors.
- Use only information provided.
- Do not exceed 10 sentences total.
- Do not use emojis, bold, or italic formatting.

"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )
    except RateLimitError:
        raise ValueError(
            "OpenAI API quota or rate limit reached. "
            "Please check your usage at platform.openai.com and try again later."
        )

    draft_summary = response.choices[0].message.content

    # Polish the draft; fall back to the draft if the polish step fails.
    try:
        return evaluate_executive_summary(draft_summary)
    except Exception:
        return draft_summary

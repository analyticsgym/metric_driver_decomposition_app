"""LLM-based executive summary generation for decomposition results."""

import os
import re
from pathlib import Path
import pandas as pd
from openai import OpenAI, APIError
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def evaluate_executive_summary(summary: str) -> str:
    """Evaluate the executive summary and make improvements."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )

    client = OpenAI()

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

    response = client.responses.create(
        model="gpt-5-mini",
        input=[{"role": "user", "content": prompt}],
        reasoning={"effort": "low"},
    )
    return response.output_text


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
        ValueError: If OpenAI API key is not found or API call fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )

    client = OpenAI()

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

B. Driver Attribution (3–6 sentences)
For each driver in the table:

1. State whether the driver was a Tailwind (+) or Headwind (–).
2. State the driver's own change (e.g., “Traffic increased 12%”).
3. Explain its effect using formula logic:
- If numerator: “Because it is a numerator, this movement raised/lowered {clean_metric_name} by [Contribution].”
- If denominator: “Because it is a denominator, this movement put upward/downward pressure on {clean_metric_name} by [Contribution].”
4. Use the actual contribution value from the table.

Follow this sentence template where possible:
“[Driver] [increased/decreased] by X%, acting as a [Tailwind/Headwind]. Because it is a [numerator/denominator], this movement [increased/decreased] {clean_metric_name} by [Contribution].”

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

    response = client.responses.create(
        model="gpt-5",
        input=[{"role": "user", "content": prompt}],
        # tools=[{"type": "web_search"}],
        # tool_choice="auto",
        reasoning={"effort": "medium"},
    )
    summary = response.output_text
    improved_summary = evaluate_executive_summary(summary)
    return improved_summary

# Sub-Metrics Driver Decomposition App

A Streamlit application that uses log decomposition to analyze time-window vs. time-window changes in business outcome metrics, based on driver sub-metric contributions.

## Features

- **Multiplicative metric decomposition**: Analyze how changes in driver metrics contribute to changes in outcome metrics (e.g., Sales, ROAS)
- **Interactive UI**: Select metrics, input time-period values, and view results
- **Waterfall visualization**: Visualize cumulative driver impacts in a waterfall chart
- **Executive summary generation**: Generate AI-powered executive summaries of decomposition results (experimental)
- **Automatic validation**: Ensures driver contributions mathematically sum to total metric change
- **Persistent results**: Decomposition results persist across interactions, allowing you to generate summaries without losing data

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key (for executive summary feature):
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

### How It Works

1. **Select a metric**: Choose from configured outcome metrics (e.g., Sales, ROAS)
2. **Input values**: Enter driver values for Time 0 and Time 1 periods
3. **Run decomposition**: Click "Run Decomposition" to analyze the changes
4. **View results**: Review the outcome metric summary, driver contributions table, and waterfall chart
5. **Generate summary** (optional): Click "Generate Executive Summary" to create an AI-powered analysis

## Configuration

Edit `config/formulas.yaml` to add or modify metric formulas:

```yaml
Sales_1: "Spend / CPA * AOV"
Sales_2: "Spend * ROAS"
ROAS_1: "AOV / CPA"
ROAS_3: "Sales / Spend"
```

Formulas support multiplication (`*`) and division (`/`) operations. Drivers in the numerator have a direct effect on the metric, while drivers in the denominator have an inverse effect.

## Project Structure

```
metric_driver_decomposition_app/
├── app.py                 # Main Streamlit application
├── README.md
├── requirements.txt
├── .gitignore
│
├── config/
│   └── formulas.yaml      # Metric formulas configuration
│
├── src/
│   ├── __init__.py
│   ├── formulas.py        # Formula parsing and evaluation
│   ├── decomposition.py   # Log decomposition mathematics
│   ├── plotting.py        # Waterfall chart visualization
│   ├── utils.py           # Validation and formatting utilities
│   └── llm_summary.py     # Executive summary generation
│
└── tests/
    ├── __init__.py
    ├── test_formulas.py
    └── test_decomposition.py
```

## Running Tests

```bash
pytest tests/
```

## Future TODOs

The following improvements are planned for future versions:

- **Continue testing for bugs/validation**: Expand test coverage and edge case handling
- **Add other metrics**: Support additional business metrics and formula types
- **Enhanced visualization**: Additional chart types potentially and export capabilities
- **Data import**: Support CSV/Excel file imports for bulk analysis
- **Historical comparisons**: Compare multiple time periods side-by-side
- **Export functionality**: Download results and summaries as PDF or Excel files

## Module Overview

- **`src/formulas.py`**: Parses formula strings and evaluates them with driver values
- **`src/decomposition.py`**: Performs multiplicative log-share decomposition
- **`src/plotting.py`**: Creates waterfall charts showing driver contributions
- **`src/utils.py`**: Validation and formatting utilities
- **`src/llm_summary.py`**: Generates executive summaries using OpenAI API

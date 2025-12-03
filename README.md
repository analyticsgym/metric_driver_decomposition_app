# Streamlit Log Decomposition App

A modular Streamlit application for decomposing multiplicative metrics (Sales, ROAS, etc.) into driver contributions using log-share decomposition.

## Project Structure

```
streamlit-log-decomp/
├── app.py                 # Main Streamlit application (thin controller)
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
│   ├── plotting.py        # Visualization functions
│   └── utils.py           # Utility functions
│
└── tests/
    ├── __init__.py
    ├── test_formulas.py
    └── test_decomposition.py
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

## Features

- **Formula-based metrics**: Define metrics using multiplicative formulas (e.g., `Sales = Spend / CPA * AOV`)
- **Log decomposition**: Attribute changes in metrics to individual driver contributions
- **Waterfall visualization**: Visualize cumulative driver impacts from t0 to t1
- **Automatic validation**: Ensures driver contributions sum to total metric change

## Configuration

Edit `config/formulas.yaml` to add or modify metric formulas:

```yaml
Sales: "Spend / CPA * AOV"
ROAS: "AOV / CPA"
CPA: "CPM / (CTR * CVR * 1000)"
```

## Running Tests

```bash
pytest tests/
```

## Module Overview

- **`src/formulas.py`**: Parses formula strings and evaluates them with driver values
- **`src/decomposition.py`**: Performs multiplicative log-share decomposition
- **`src/plotting.py`**: Creates waterfall charts showing driver contributions
- **`src/utils.py`**: Validation and formatting utilities


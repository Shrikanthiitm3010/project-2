# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "seaborn",
#   "httpx",
#   "chardet",
#   "matplotlib",
#   "pandas"
# ]
# ///

import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import httpx
import chardet

# Constants
API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
AIPROXY_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIyZjIwMDE0MDFAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.W2kWL_ocDqo7SnQyHnA2CArX9Qk5alEffFZRHEi957Y"

def load_data(file_path):
    """Load CSV data with encoding detection."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    encoding = result['encoding']
    return pd.read_csv(file_path, encoding=encoding)

def analyze_data(df):
    """Perform advanced data analysis."""
    numeric_df = df.select_dtypes(include=['number'])
    categorical_df = df.select_dtypes(include=['object', 'category'])

    # Summary for numeric columns
    numeric_summary = {
        'mean': numeric_df.mean().to_dict(),
        'median': numeric_df.median().to_dict(),
        'mode': numeric_df.mode().iloc[0].to_dict(),
        'skewness': numeric_df.skew().to_dict(),
        'kurtosis': numeric_df.kurt().to_dict(),
        'standard_deviation': numeric_df.std().to_dict()
    }

    # Summary for categorical columns
    categorical_summary = {
        column: df[column].value_counts().to_dict()
        for column in categorical_df.columns
    }

    analysis = {
        'numeric_summary': numeric_summary,
        'categorical_summary': categorical_summary,
        'missing_values': df.isnull().sum().to_dict(),
        'correlation': numeric_df.corr().to_dict()
    }
    return analysis

def detect_outliers(df):
    """Detect outliers in numeric data."""
    outliers = {}
    for column in df.select_dtypes(include=['number']).columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers[column] = df[(df[column] < lower_bound) | (df[column] > upper_bound)].shape[0]
    return outliers

def visualize_data(df):
    """Generate enhanced visualizations."""
    sns.set(style="whitegrid")
    numeric_columns = df.select_dtypes(include=['number']).columns

    for column in numeric_columns:
        plt.figure(figsize=(8, 5))
        sns.histplot(df[column].dropna(), kde=True, color="blue", alpha=0.7)
        plt.axvline(df[column].mean(), color='red', linestyle='dashed', label='Mean')
        plt.axvline(df[column].median(), color='green', linestyle='dashed', label='Median')
        plt.title(f'Distribution of {column}')
        plt.legend()
        plt.savefig(f'{column}_distribution.png')
        plt.close()

        plt.figure(figsize=(8, 5))
        sns.boxplot(data=df[column], orient='h')
        plt.title(f'Boxplot for {column}')
        plt.savefig(f'{column}_boxplot.png')
        plt.close()

def visualize_correlation(df):
    """Visualize correlations among numeric features."""
    numeric_df = df.select_dtypes(include=['number'])
    plt.figure(figsize=(10, 8))
    corr_matrix = numeric_df.corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
    plt.title('Correlation Heatmap')
    plt.savefig('correlation_heatmap.png')
    plt.close()

def generate_narrative(analysis):
    """Generate detailed narrative."""
    headers = {
        'Authorization': f'Bearer {AIPROXY_TOKEN}',
        'Content-Type': 'application/json'
    }
    prompt = f"""
    Provide a detailed analysis based on the following data:
    - Summary statistics: {analysis['numeric_summary']}
    - Missing values: {analysis['missing_values']}
    - Correlation matrix: {analysis['correlation']}
    """
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = httpx.post(API_URL, headers=headers, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
    except httpx.RequestError as e:
        print(f"Request error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return "Narrative generation failed due to an error."

def main(file_path):
    folder_name = file_path.split(('/'))[-1].split('.')[0]
    os.makedirs(folder_name, exist_ok=True)
    os.chdir(folder_name)

    df = load_data(file_path)
    analysis = analyze_data(df)
    outliers = detect_outliers(df)
    visualize_data(df)
    visualize_correlation(df)

    narrative = generate_narrative(analysis)
    print(narrative)

    with open('README.md', 'w') as f:
        f.write(narrative)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    main(sys.argv[1])

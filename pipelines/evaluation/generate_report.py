"""
Script to generate evaluation reports.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_latest_evaluation_results(evaluation_type: str) -> Dict[str, Any]:
    """
    Load the latest evaluation results for a given type.

    Args:
        evaluation_type: Type of evaluation ('candidate_generation', 'ranking', etc.)

    Returns:
        Dictionary of evaluation results.
    """
    evaluation_dir = f"./evaluation/reports/{evaluation_type}"
    if not os.path.exists(evaluation_dir):
        logger.warning(f"Evaluation directory {evaluation_dir} does not exist")
        return {}

    # Find the latest evaluation file
    files = [f for f in os.listdir(evaluation_dir) if f.endswith('.json')]
    if not files:
        logger.warning(f"No evaluation files found in {evaluation_dir}")
        return {}

    latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(evaluation_dir, f)))
    latest_file_path = os.path.join(evaluation_dir, latest_file)

    try:
        with open(latest_file_path, 'r') as f:
            results = json.load(f)
        logger.info(f"Loaded evaluation results from {latest_file_path}")
        return results
    except Exception as e:
        logger.error(f"Error loading evaluation results from {latest_file_path}: {e}")
        return {}

def generate_html_report(candidate_results: Dict[str, Any],
                         ranking_results: Dict[str, Any],
                         output_file: str = "./evaluation/reports/latest_report.html"):
    """
    Generate an HTML report from evaluation results.

    Args:
        candidate_results: Candidate generation evaluation results.
        ranking_results: Ranking evaluation results.
        output_file: Path to save the HTML report.
    """
    logger.info(f"Generating HTML report to {output_file}")

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recommendation System Evaluation Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1, h2, h3 { color: #2c3e50; }
            .section { margin-bottom: 30px; }
            .metric { margin: 10px 0; }
            .good { color: #27ae60; }
            .fair { color: #f39c12; }
            .poor { color: #e74c3c; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h1>Recommendation System Evaluation Report</h1>
        <p>Generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    """

    # Candidate Generation Section
    html_content += """
        <div class="section">
            <h2>Candidate Generation Evaluation</h2>
    """
    if candidate_results and "error" not in str(candidate_results):
        html_content += """
            <table>
                <tr>
                    <th>Generator</th>
                    <th>Hit@1</th>
                    <th>Hit@5</th>
                    <th>Hit@10</th>
                    <th>MRR</th>
                </tr>
        """
        for generator, metrics in candidate_results.items():
            if "error" not in metrics:
                hit_at_1 = metrics.get('hit_at_1', 0)
                hit_at_5 = metrics.get('hit_at_5', 0)
                hit_at_10 = metrics.get('hit_at_10', 0)
                mrr = metrics.get('mrr', 0)

                # Determine CSS class based on performance
                def get_class(value):
                    if value >= 0.7:
                        return "good"
                    elif value >= 0.4:
                        return "fair"
                    else:
                        return "poor"

                html_content += f"""
                <tr>
                    <td>{generator}</td>
                    <td class="{get_class(hit_at_1)}">{hit_at_1:.4f}</td>
                    <td class="{get_class(hit_at_5)}">{hit_at_5:.4f}</td>
                    <td class="{get_class(hit_at_10)}">{hit_at_10:.4f}</td>
                    <td class="{get_class(mrr)}">{mrr:.4f}</td>
                </tr>
                """
            else:
                html_content += f"""
                <tr>
                    <td>{generator}</td>
                    <td colspan="4" style="color: red;">Error: {metrics.get('error', 'Unknown error')}</td>
                </tr>
                """
        html_content += "</table>"
    else:
        html_content += "<p>No candidate generation evaluation results available.</p>"

    html_content += "</div>"

    # Ranking Section
    html_content += """
        <div class="section">
            <h2>Ranking Model Evaluation</h2>
    """
    if ranking_results and "error" not in str(ranking_results):
        html_content += """
            <table>
                <tr>
                    <th>Ranker</th>
                    <th>NDCG@1</th>
                    <th>NDCG@3</th>
                    <th>NDCG@10</th>
                    <th>MSE</th>
                </tr>
        """
        for ranker, metrics in ranking_results.items():
            if "error" not in metrics:
                ndcg_1 = metrics.get('ndcg@1', 0)
                ndcg_3 = metrics.get('ndcg@3', 0)
                ndcg_10 = metrics.get('ndcg@10', 0)
                mse = metrics.get('mse', 0)

                # Determine CSS class based on performance (lower MSE is better)
                def get_class_for_ndcgdcg(value):
                    if value >= 0.7:
                        return "good"
                    elif value >= 0.4:
                        return "fair"
                    else:
                        return "poor"

                def get_class_for_mse(value):
                    if value <= 0.1:
                        return "good"
                    elif value <= 0.3:
                        return "fair"
                    else:
                        return "poor"

                html_content += f"""
                <tr>
                    <td>{ranker}</td>
                    <td class="{get_class_for_ndcg(ndcg_1)}">{ndcg_1:.4f}</td>
                    <td class="{get_class_for_ndcg(ndcg_3)}">{ndcg_3:.4f}</td>
                    <td class="{get_class_for_ndcg(ndcg_10)}">{ndcg_10:.4f}</td>
                    <td class="{get_class_for_mse(mse)}">{mse:.4f}</td>
                </tr>
                """
            else:
                html_content += f"""
                <tr>
                    <td>{ranker}</td>
                    <td colspan="4" style="color: red;">Error: {metrics.get('error', 'Unknown error')}</td>
                </tr>
                """
        html_content += "</table>"
    else:
        html_content += "<p>No ranking evaluation results available.</p>"

    html_content += "</div>"

    # Summary and Recommendations
    html_content += """
        <div class="section">
            <h2>Summary and Recommendations</h2>
            <p>
                Based on the evaluation results, here are some recommendations for improving the recommendation system:
            </p>
            <ul>
                <li>Consider ensemble methods that combine multiple candidate generators</li>
                <li>Feature engineering is crucial for ranking model performance</li>
                <li>Regular evaluation and retraining help maintain model performance</li>
                <li>A/B testing should be used to validate changes in production</li>
            </ul>
        </div>
    """

    html_content += """
    </body>
    </html>
    """

    # Write to file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        f.write(html_content)

    logger.info(f"HTML report generated at {output_file}")

def main():
    """
    Main function to generate evaluation reports.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("Starting report generation")

    # Load latest evaluation results
    candidate_results = load_latest_evaluation_results('candidate_generation')
    ranking_results = load_latest_evaluation_results('ranking')

    # Generate HTML report
    generate_html_report(candidate_results, ranking_results)

    logger.info("Report generation completed")

if __name__ == "__main__":
    main()
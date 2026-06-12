"""Dashboard service — placeholder.

Responsibilities (to be implemented):
- Persist prediction results to app/data/results/
- Aggregate saved results into summary statistics
- Return data for charts (win rate trend, top products, etc.)
"""


def save_result(result: dict, results_dir: str):
    # TODO: append result to a JSON/CSV file in results_dir
    raise NotImplementedError


def get_saved_results(results_dir: str) -> list:
    # TODO: read and return all saved results
    raise NotImplementedError


def get_dashboard_summary(results_dir: str) -> dict:
    # TODO: compute aggregated stats (win rate, avg price, top sector, etc.)
    raise NotImplementedError

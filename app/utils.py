"""
Utility functions
"""
from typing import List


def calculate_median(data: List[int]) -> float:
    """Calculate median value from list of integers"""
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 0:
        return 0
    if n % 2 == 1:
        return sorted_data[n // 2]
    else:
        return (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / 2

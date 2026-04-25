"""
Output Filter for Batch Request Results

Filter batch request results based on conditions with support for:
- Nested field access (dot notation)
- Multiple operators (==, !=, >, <, in, contains, matches, is_null, has_key)
- Include/exclude modes
- Regex pattern matching

@MX:NOTE: Enables intelligent filtering of batch request results
"""

import logging
import operator
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class OutputFilter:
    """
    Filter batch request results based on conditions.

    Supports nested field access and multiple operators.

    @MX:ANCHOR: Output filtering engine for batch requests (fan_in: batch_request node)
    @MX:REASON: Single filtering logic ensures consistent condition evaluation
    """

    OPERATORS = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '<': operator.lt,
        '>=': operator.ge,
        '<=': operator.le,
        'in': lambda a, b: a in b if isinstance(b, (list, tuple, set)) else False,
        'not_in': lambda a, b: a not in b if isinstance(b, (list, tuple, set)) else True,
        'contains': lambda a, b: b in str(a),
        'not_contains': lambda a, b: b not in str(a),
        'is_null': lambda a, b: a is None,
        'is_not_null': lambda a, b: a is not None,
        'has_key': lambda a, b: isinstance(a, dict) and b in a,
    }

    def __init__(self, filter_config: Dict[str, Any]):
        """
        Args:
            filter_config: {
                "mode": "include" | "exclude",
                "conditions": [
                    {"field": "response.status", "operator": "==", "value": 200},
                    {"field": "response.data.user.name", "operator": "contains", "value": "John"}
                ]
            }
        """
        self.mode = filter_config.get("mode", "include")
        self.conditions = filter_config.get("conditions", [])

    def get_nested_value(self, obj: Any, field_path: str) -> Any:
        """
        Get value from nested object using dot notation.

        Examples:
            >>> get_nested_value({"a": {"b": {"c": 1}}}, "a.b.c")
            1
            >>> get_nested_value({"response": {"data": [1,2,3]}}, "response.data.0")
            1
        """
        keys = field_path.split('.')
        value = obj

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif isinstance(value, list) and key.isdigit():
                index = int(key)
                value = value[index] if 0 <= index < len(value) else None
            else:
                return None

            if value is None:
                return None

        return value

    def matches_regex(self, value: Any, pattern: Optional[str]) -> bool:
        """Check if value matches regex pattern"""
        if not pattern:
            return True
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            return False

    def evaluate_condition(self, row: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """
        Evaluate single condition against row.

        Args:
            row: Result row from batch request
            condition: Condition specification

        Returns:
            True if condition matches, False otherwise
        """
        field = condition["field"]
        op = condition["operator"]
        expected = condition.get("value")

        # Get actual value from nested field
        actual = self.get_nested_value(row, field)

        # Handle regex operators
        if op in ["matches", "not_matches"]:
            result = self.matches_regex(actual, expected)
            return result if op == "matches" else not result

        # Handle null checks (value not used)
        if op in ["is_null", "is_not_null"]:
            return self.OPERATORS[op](actual, None)

        # Handle key existence (value is the key name)
        if op == "has_key":
            # Extract parent object and key name
            field_parts = field.split('.')
            if len(field_parts) > 1:
                parent_path = '.'.join(field_parts[:-1])
                parent_obj = self.get_nested_value(row, parent_path)
                return self.OPERATORS[op](parent_obj, expected)
            else:
                return self.OPERATORS[op](row, expected)

        # Standard operators
        if op not in self.OPERATORS:
            raise ValueError(f"Unknown operator: {op}")

        try:
            return self.OPERATORS[op](actual, expected)
        except (TypeError, ValueError) as e:
            logger.warning(
                f">>> [OUTPUT FILTER] Condition evaluation failed: "
                f"{field} {op} {expected} - {e}"
            )
            return False

    def filter(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter rows based on conditions.

        In 'include' mode: row must match ALL conditions (AND)
        In 'exclude' mode: exclude rows that match ANY condition (OR)

        Args:
            rows: List of result rows from batch request

        Returns:
            Filtered list of rows
        """
        if not self.conditions:
            return rows

        filtered = []

        for row in rows:
            if self.mode == "include":
                # Include if ALL conditions match (AND logic)
                matches = all(
                    self.evaluate_condition(row, cond)
                    for cond in self.conditions
                )
                if matches:
                    filtered.append(row)

            else:  # exclude mode
                # Exclude if ANY condition matches (OR logic)
                matches = any(
                    self.evaluate_condition(row, cond)
                    for cond in self.conditions
                )
                if not matches:
                    filtered.append(row)

        return filtered

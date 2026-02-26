from .tools import (
    detect_disruption_tool,
    company_policy_tool,
    search_alternative_flights_tool,
    rank_flights_tool,
)


class DisruptionAgent:
    """
    Responsible for disruption detection.
    """

    def analyze(self, departure_time, disruption_type=None):

        if disruption_type and disruption_type != "auto":
            return disruption_type

        return detect_disruption_tool(departure_time)


class PolicyAgent:
    """
    Responsible for corporate policy validation.
    """

    def validate(self, price: float):
        return company_policy_tool(price)


class RebookingAgent:
    """
    Responsible for searching and ranking alternatives.
    """

    def find_best_option(self, origin: str, destination: str):

        flights = search_alternative_flights_tool(origin, destination)

        if not flights:
            return None

        ranked_flights = rank_flights_tool(flights)

        return ranked_flights[0]
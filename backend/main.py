from crewai import Task, Crew
from backend.agents import build_agents
from backend.tools import (
    simulate_disruption,
    get_itinerary,
    get_policy,
    search_alternatives
)

def run_crew_workflow(request):
    monitoring_agent, impact_agent, policy_agent, rebooking_agent = build_agents()

    pnr = request.pnr
    itinerary = get_itinerary(pnr)
    policy = get_policy()
    disruption_status = simulate_disruption(pnr)

    monitoring_task = Task(
        description=f"""
        Monitor itinerary for employee {request.employee_name}.
        Itinerary: {itinerary}
        Disruption Status: {disruption_status}
        Identify disruption type and risk.
        """,
        agent=monitoring_agent,
        expected_output="Clear disruption analysis"
    )

    impact_task = Task(
        description=f"""
        Disruption: {disruption_status}
        Analyze business impact considering meeting urgency and delay.
        Classify impact: Minor, Moderate, Critical.
        """,
        agent=impact_agent,
        expected_output="Impact severity with reasoning"
    )

    policy_task = Task(
        description=f"""
        Corporate Policy: {policy}
        Available Flights: {search_alternatives()}
        Filter policy-compliant flights only.
        """,
        agent=policy_agent,
        expected_output="List of compliant flights"
    )

    rebooking_task = Task(
        description=f"""
        Choose best rebooking option from: {search_alternatives()}
        Prioritize earliest arrival, cost efficiency, and policy compliance.
        """,
        agent=rebooking_agent,
        expected_output="Final best flight recommendation"
    )

    crew = Crew(
        agents=[monitoring_agent, impact_agent, policy_agent, rebooking_agent],
        tasks=[monitoring_task, impact_task, policy_task, rebooking_task],
        verbose=True
    )

    result = crew.kickoff()
    return result
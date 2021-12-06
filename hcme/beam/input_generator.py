from hcme.demand.reactor import build_travel_diary


def generate_experiment_inputs(experiment):
    build_travel_diary(
        experiment.demand_scenario.pct_vehicle_ownership,
        experiment.demand_scenario.name,
    )

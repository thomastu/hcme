from hcme.demand.reactor import build_travel_diary


def generate_experiment_inputs(experiment):
    # Generate travel diaries
    build_travel_diary(
        experiment.demand_scenario.pct_vehicle_ownership,
        experiment.demand_scenario.name,
    )

    # Generate Fleets
    build_microtransit_fleet(size)

    # Generate configuration

    build_config_file(**experiment.settings)

# Overview

The HCME (Humboldt County Microtransit Evaluation) is a research project pursuant toward my Master's thesis. The purpose of this project is two fold -

1.  Demonstrate the utility of agent based modeling in evaluating new mobility technologies using the BEAM model: https://beam.readthedocs.io
2.  Evaluate how microtransit/public ridehail would impact mobility and transportation services in Humboldt County, a largely rural region with no metropolitan population centers and limited public transit investment.

The accompanying thesis will be linked and made public here as well.

# Developer Quickstart

## Install System Dependencies

The following system dependencies are required:

- postgres
- PostGIS
- GDAL
- osmosis
- python3.9+
- A BEAM compatible version of JAVA
- The BEAM application downloaded somewhere on your machine

## Install Application

This research project is packaged as a python project using `poetry`.  Several critical libraries are python bindings for geospatial system libraries (such as GDAL.)

```
poetry install # This will install the `hcme` entrypoint
# Active virtual env or use `poetry run`
# poetry shell 
```

## Configuration

```
createdb hcme
hcme migrate

# Create a `settings.local.toml` file with db credentials

# Run BEAM
# hcme beam -c /path/to/beam.conf -r 24G
```


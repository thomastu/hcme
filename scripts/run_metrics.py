"""
Run summary statistics and export data
"""

from hcme.demand import summary
from hcme.metrics import export

if __name__ == "__main__":

    demand_matrix = summary.DemandMatrix(top_n=10)
    demand_matrix.run()

    # Export data
    export(domain=summary.domain, default_hooks=["csv"])

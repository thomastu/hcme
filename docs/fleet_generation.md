# Fleet Generation

Fleet generation consisted of three major components:

1. An algorithm to partition the analysis zone into regions of interest
2. A metric to determine priority of fleet placement within each region
3. Fleet characteristics including
  - fleet size
  - BEAM vehicle type to use
  - service range 
  - operating hours



Two methods were deployed to generate regional partitions:

The first relied on creating zones out of the existing public transit network (using bus stops listed in the GTFS.) Using existing stop locations, Voronoi regions were generated for each stop and combined with household locations to generate cohorts of potential riderships based on 2 parameters.  The minimum distance for a household to use microtransit and the maximum operating service range.  For example, a minimum distance of 0.25 miles and a service range of 2 miles would result in households that live 0.25 miles or more from their nearest fixed-route transit stop but more than 2 miles. Fleet vehicles were then distributed such that each assignment went to the least served and greatest density region measured in fleet vehicles per household per square mile. That is, given 2 equally populated regions with a density of 100 households per sq. mile, and 10 households per sq. mile, a vehicle would be distributed to the former.

The second family of scenarios looked at the use of microtransit as a list mile transit option. To generate fleets to serve last mile trips

1. Filter for all trips greater than a minimum walking range, but less than a maximum service range (e.g. 0.25 miles to 2 miles)
2. Cluster the set of filtered trips and distribute microtransit vehicles to maximize the number of people per vehicles in each cluster.
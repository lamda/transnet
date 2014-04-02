TransNet
==============================

TransNet is tool to analyze centralities in the public transit network of Graz, Austria. It loads data from files dumped from OpenStreetMap and schedule information from the Verbundlinie, and uses Python (and the networkx library) to construct a public transit network consisting of stops and connections between them. It then calculates several centrality measures (closeness centrality, geographical closeness centrality and traveltime centrality) on the network and identifies the most central nodes based on these measures.

The data is available in the data folder. The schedule information was obtained manually from the [Verbundlinie](http://www.verbundlinie.at) (CC-BY). The rest of the data was obtained from the OpenStreetMap [Overpass Turbo API](http://overpass-turbo.eu/) (© OpenStreetMap contributors, [ODbL](http://www.openstreetmap.org/copyright)). The data was obtained by first selecting an area that includes Graz and some of its surroundings and then running the following queries:

Tramway network (data/osm_tram_traveltimes.xml)
========

```
<union>
<query type="relation">
  <has-kv k="type" v="route"/>
  <has-kv k="route" v="tram"/>
  <has-kv k="alternate" v="no"/>
  <bbox-query {{bbox}}/>
  </query>
  
<query type="node">
  <has-kv k="public_transport" v="stop_position"/>
  <has-kv k="railway" v="tram_stop"/>
  <bbox-query {{bbox}}/>
</query>
</union>

<print mode="meta"/>
```

Urban Bus Network (data/osm_bus_traveltimes.xml)
========

```

<union>
<query type="node">
  <has-kv k="highway" v="bus_stop"/>
  <bbox-query {{bbox}}/>
</query>
  
<query type="node">
    <has-kv k="railway" v="tram_stop"/>
  <bbox-query {{bbox}}/>
</query>
  
<query type="node">
    <has-kv k="public_transport" v="platform"/>
  <bbox-query {{bbox}}/>
</query>
  
  
<query type="relation">
  <has-kv k="type" v="route"/>
  <has-kv k="route" v="bus"/>
  <has-kv k="alternate" v="no"/>
  <bbox-query {{bbox}}/>
</query> 

<query type="relation">
  <has-kv k="type" v="route"/>
  <has-kv k="route" v="tram"/>
  <has-kv k="alternate" v="no"/>
  <bbox-query {{bbox}}/>
  </query> 

</union>

<print mode="meta"/>
```


Suburban Train Network (data/osm_sbahn_traveltimes.xml)
========
This data set was initialized from an API query but then mostly compiled by hand. In this way, only train stops in fare zone 101 are included, and the stop names are equal to the names of tram and bus stops.

Remarks
========
The schedule data is valid for a workday between 7-8 am. Accordingly, the network consists of all lines operating in these hours. The network is furthermore restricted to fare zone 101 (Graz and surroundings) and excludes suburban buses ("Regionalbusse") as special rules apply for these lines for boarding and alighting.

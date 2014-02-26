Transnet
==============================

Transnet is tool to analyze data from the public transit network of Graz, Austria. It loads data from files dumped from OpenStreetMap, constructs a networkx graph and calculates several centrality measures (betweenness centrality, eigenvector centrality, geodesic closeness centrality).

The data is available in the data folder and was obtained from the OpenStreetMap [Overpass Turbo API](http://overpass-turbo.eu/) in 2013. All data is © OpenStreetMap contributors, [ODbL](http://www.openstreetmap.org/copyright). The data was obtained by first selecting an area that includes Graz and some of its surroundings and then running the following queries:

Tramway network (data/osm_tram.xml)
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

Tramway + Urban Bus Network (data/osm_tram_bus.xml)
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


Suburban Train Network (data/osm_sbahn.xml)
========
This data set was initialized from an API query but then mostly compiled by hand. In this way, only train stops in fare zone 101 are included, and the stop names are equal to the names of tram and bus stops. Note that this includes all stops but not all suburban train lines (many of which share stops).

Task: Given an Inital Path and some feedback information of a Question, please correct the initial path.
-----
Question: where is aviano air force base located?
Initial Path: aviano air force base -> place.place.location
>>>> Error Message
1. relation "place.place.location" not instantiated.
>>>> Instantiation Context
Instantiate Paths:
Candidate Relations: ['aviation.airport.serves', 'base.aareas.schema.administrative_area.administrative_children', 'base.aareas.schema.administrative_area.administrative_parent', 'base.popstra.location.vacationers', 'base.popstra.vacation_choice.location', 'base.wikipedia_infobox.settlement.area_code', 'book.newspaper.circulation_areas', 'broadcast.broadcast.area_served', 'film.film.featured_film_locations', 'film.film_location.featured_in_films', 'location.hud_county_place.county', 'location.hud_county_place.place', 'location.hud_foreclosure_area.hhuniv', 'location.hud_foreclosure_area.ofheo_price_change', 'location.hud_foreclosure_area.total_90_day_vacant_residential_addresses', 'location.location.area', 'location.location.containedby', 'location.location.geolocation', 'location.location.gnis_feature_id', 'location.location.nearby_airports', 'location.location.time_zones', 'location.mailing_address.citytown', 'location.us_county.hud_county_place', 'organization.organization.place_founded', 'people.deceased_person.place_of_death', 'people.marriage.location_of_ceremony', 'people.place_lived.location', 'transportation.bridge.locale', 'transportation.road_starting_point.location', 'travel.tourist_attraction.near_travel_destination', 'travel.transportation.travel_destination', 'travel.travel_destination.how_to_get_here', 'travel.travel_destination.tourist_attractions', 'tv.tv_location.tv_shows_filmed_here', 'tv.tv_program.filming_locations']
>>>> Corrected Path
Goal: The Initial Path is from aviano air force base, which should cover the place it located.
Thought: In candidates, I find "location.location.containedby" most relevant to the place air force base located.
Final Path: aviano air force base -> location.location.containedby
-----
Question: what major airport is near destin florida?
Initial Path: destin florida -> place.place.airports_near -> airport.airport.major_airport
>>>> Error Message
1. relation "airport.airport.major_airport" not instantiated.
>>>> Instantiation Context
Instantiate Paths: destin florida -> location.location.nearby_airports -> Destin–Fort Walton Beach Airport
destin florida -> location.location.nearby_airports -> Destin Executive Airport
Candidate Relations: ['aviation.airline.focus_cities', 'aviation.airline.hubs', 'aviation.airport.focus_city_for', 'aviation.airport.hub_for', 'aviation.airport.iata', 'aviation.airport.icao', 'aviation.airport.number_of_runways', 'aviation.airport.serves', 'base.ourairports.airport.ourairports_id', 'kg.object_profile.prominent_type', 'location.location.containedby', 'location.location.contains', 'location.location.geolocation', 'location.location.nearby_airports', 'location.location.time_zones', 'time.time_zone.locations_in_this_time_zone', 'travel.transportation.mode_of_transportation']
>>>> Corrected Path
Goal: The Initial Path is from destin florida, which should cover the airports near destin florida and then the number of runways to know the major one.
Thought: In Instantiate Paths, I know that destin florida has some nearby airports.
In candidates, I find "aviation.airport.number_of_runways" most relevant to number of runways.
Final Path: destin florida -> place.place.airports_near -> aviation.airport.number_of_runways
-----
Question: what to see outside of paris?
Initial Path: paris -> location.location.near_by
>>>> Error Message
1. <cvt></cvt> in the end. 
>>>> Instantiation Context
Instantiate Paths: paris -> location.location.adjoin_s -> <cvt></cvt>
Candidate Relations: ['location.adjoining_relationship.adjoins']
>>>> Corrected Path
Goal: The Initial Path is from paris, which should cover some tourism attractions in paris.
Thought: In Instantiate Paths, I know that paris adjoins some place, described by a cvt node.
Some candidates are given. However, I want some tourism attractions in this path.
Final Path: paris -> travel.travel_destination.tourist_attractions
-----
Question: where did laura ingalls wilder live?
Initial Path: laura ingalls wilder -> people.person.places_lived
>>>> Error Message
1. <cvt></cvt> in the end. 
>>>> Instantiation Context
Instantiate Paths: laura ingalls wilder -> people.person.places_lived -> <cvt></cvt>
Candidate Relations: ['people.person.places_lived', 'people.place_lived.location', 'people.place_lived.person']
>>>> Corrected Path
Goal: The Initial Path is from laura ingalls wilder, which should cover the place he lived.
Thought: In Instantiate Paths, I know that laura ingalls wilder lived in some place, described by a cvt node.
In candidates, I find "people.place_lived.location" most relevant to get place he lived.
Final Path: laura ingalls wilder -> people.person.places_lived -> people.place_lived.location
-----
Question: who played princess leia in star wars movies?
Initial Path: princess leia -> film.film.actor
>>>> Error Message
1. <cvt></cvt> in the end. 
>>>> Instantiation Context
Instantiate Paths: princess leia -> film.performance.character -> <cvt></cvt>
Candidate Relations: ['film.actor.film', 'film.film.starring', 'film.film_character....d_in_films', 'film.performance.actor', 'film.performance.film']
>>>> Corrected Path
Goal: The Initial Path is from princess leia, which should cover the film it is in, and then the actor if the film.
Thought: In Instantiate Paths, I know that princess leia is in some films, described by a cvt node.
In candidates, I find "film.performance.actor" most relevant to get place he lived.
Final Path: laura ingalls wilder -> film.performance.character -> film.performance.actor
-----

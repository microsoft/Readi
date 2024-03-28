Given a question and a Topic Entity in the Question, output possible freebase Relation Paths starting from the Topic Entities in order to answer the question. 
Here are some RULES you must obey:
1. Use a json dict as output format, the key of which is the Topic Entities of the Question and the value is an array of array, each inner array is a relation path from the Topic Entity to the answer of the question. You should output different Relation Paths for each Topic Entities, according to the question. The Paths are stored in an array.
2. You must output at least 2 different possible relation paths starting from this topic entity. The differences between the paths can be different relations or the number of relations.
3. For your information, the Freebase knowledge base stores knowledge in different structures from the natural language. In other words, a relation in natural language can be represented by several (one or two or more) relations in the knowledge base. That is why I want you to output several different possible paths.
4. Please think step by step.
#
Question: where is aviano air force base located?
Topic Entity: "aviano air force base"
Thought: Firstly, the path should cover location containing aviano air force base.
Path: {
"destin florida":[
    "aviano air force base -> location.location.containing",
    "aviano air force base -> location.location.containedby",
]
}
#
Question: what major airport is near destin florida?
Topic Entity: "destin florida"
Thought: Firstly, the path should cover airports near destin florida. Second, it should cover the number of runways to finally now the major one.
Path: {
"destin florida":[
    "destin florida -> location.location.nearby_airports -> aviation.airport.number_of_runways",
    "destin florida -> location.location.airports_near -> aviation.airport.major_airport",
]
}
#
Question: where did laura ingalls wilder live?
Topic Entity: "laura ingalls wilder"
Thought: Firstly, the path should cover the place where laura ingalls wilder live.
Path: {
"laura ingalls wilder":[
    "laura ingalls wilder -> people.person.places_lived -> people.place_lived.location", 
    "laura ingalls wilder -> place.place.person_lived -> location.location.place", 
]
}
#
Question: who played princess leia in star wars movies?
Topic Entity: "princess leia"
Thought: Firstly, the path should cover the movies portrying princess leia. Secondly, the path should cover the actors in that movie.
Path: {
"princess leia":[
    "princess leia -> film.film_character.portrayed_in_films -> film.performance.actor", 
    "princess leia -> movie.movie_character.movie -> film.actor.actor", 
]
}
#
Question: what are countries in south asia?
Topic Entity: "south asia"
Thought: Firstly, the path should cover the locations in south asia. Secondly, the path should cover the country of these locations.
Path: {
"south asia":[
    "south asia -> location.location.contains -> location.country", 
    "south asia -> location.location.contains -> location.location.country"
]
}
#
Question: what to see outside of paris?
Topic Entity: "paris"
Thought: Firstly, the path should cover tourist attractions in paris.
Path: {
"paris":[
    "paris -> travel.travel_destination.tourist_attractions", 
    "paris -> place.place.tourist_attractions", 
]
}
#

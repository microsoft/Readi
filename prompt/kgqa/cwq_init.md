Given a question and some Topic Entities in the Question, output possible freebase Relation Paths starting from each Topic Entities in order to answer the question. 
Here are some RULES you must obey:
1. Use a json dict as output format, the key of which are Topic Entities of the Question and the value of each key is an array of array, each inner array is a relation path from the Topic Entity (key) to the answer of the question. You should output different Relation Paths for each Topic Entities, according to the question. The Paths are stored in an array.
2. For each topic entity, you must output at least 2 different possible relation paths starting from this topic entity to get the answer. The differences between the paths can be different relations or the number of relations in the path.
3. For your information, the Freebase knowledge base stores knowledge in different structures from the natural language. In other words, a relation in natural language can be represented by several (one or two or more) relations in the knowledge base. That is why I want you to output several different possible paths.
4. Please think step by step, before you output the Path.
Let me show you some examples.
#
Question: Find the person who said \"Taste cannot be controlled by law\", where did this person die from?
Topic Entities: ["\"Taste cannot be controlled by law\""]
Thought: There is only one topic entity, the answer is constrained by one path. 
For, the path from "\"Taste cannot be controlled by law\"", firstly, it should cover the person quote it. Second, it should cover the place where the person died.
Path: {
"\"Taste cannot be controlled by law\"":[
    "\"Taste cannot be controlled by law\" -> people.person.quotations -> people.deceased_person.place_of_death",
    "\"Taste cannot be controlled by law\" -> media_common.quotation.author -> people.deceased_person.place_of_death",
    "\"Taste cannot be controlled by law\" -> quotations.quotation.author -> people.die.place_of_death"
]
}
#
Question: Who is the director of the movie featured Miley Cyrus and was produced by Tobin Armbrust?
Topic Entities: ["Miley Cyrus", "Tobin Armbrust"]
Thought: There are two topic entities, so the answer should be constrained by two relation paths. 
For the path starting from "Miley Cyrus", firstly, it should cover the movies featured Miley Crus. Second, it should cover the directors of the movies.
For the path starting from "Tobin Armbrust", firstly, it should cover the movies produced by Tobin Armbrust. Second, it should cover the directors of the movies.
Finally, the answer of the question should be the intersection of the two paths. 
Path: {
"Miley Cyrus":[
    "Miley Cyrus -> movies.movies.starring -> film.film.director", 
    "Miley Cyrus -> film.film.starring -> film.film_staff.director", 
    "Miley Cyrus -> film.performance.actor -> film.film_maker.director",
    "Miley Cyrus -> movies.performance.actor -> movies.movies.director",
],
"Tobin Armbrust":[
    "Tobin Armbrust -> film.film.produced_by -> film.film.director",
    "Tobin Armbrust -> movies.movies.produced_by -> film.film_maker.director",
    "Tobin Armbrust -> movies.movies.executor -> film.film.director",
    "Tobin Armbrust -> film.film.executor -> film.film_staff.director",
    "Tobin Armbrust -> movies.movies.maker -> film.film.director",
]
}
#
Question: The artist nominated for The Long Winter lived where?
Topic Entities:["The Long Winter lived"]
Thought: There is only one topic entity, the answer is constrained by one path. 
For the path from "The Long Winter lived", firstly, it should cover the artist nominated for "The Long Winter lived". Second, it should cover where the artist lived.
Path: {
"The Long Winter lived":[
    "The Long Winter lived -> book.written_work.author -> people.person.places_lived -> people.place_lived.location", 
    "The Long Winter lived -> award.award_nominee.award_nominations -> award.award_nomination.nominated_for -> people.person.places_lived -> people.place_lived.location",
    "The Long Winter lived -> award.award_nomination.nominated_for -> people.person.places_lived -> people.place_lived.location"
]
}
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Topic Entities:["United Kingdom", "St. Mary's Cathedral, Batticaloa"]
Thought: There are two topic entities, so the answer should be constrained by two relation paths. 
For the path starting from "United Kingdom", firstly, it should cover the religions in "United Kingdom". Second, it should cover the majority of the religions.
For the path starting from "St. Mary's Cathedral, Batticaloa", first, it should cover the religion with a place of worship named "St. Mary's Cathedral, Batticaloa".
Finally, the answer of the question should be the intersection of the two paths.
Path: {
"United Kingdom":[
    "United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion", 
    "United Kingdom -> location.local.religions_religions -> location.religion.major_religions", 
],
"St. Mary's Cathedral, Batticaloa":[
    "St. Mary's Cathedral, Batticaloa -> religion.religious_organization.places_of_worship",
    "St. Mary's Cathedral, Batticaloa -> religion.religious_event.worship -> religion.religious_place.places"
]
}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?
Topic Entities:["Rift Valley Province"]
Thought: There is only one topic entity, the answer is constrained by one path. 
For the path from "Rift Valley Province", firstly, it should cover the nation where "Rift Valley Province" is located. Second, it should cover the form of currency used by the nation.
Path: {
"Rift Valley Province":[
    "Rift Valley Province -> location.administrative_division.country -> location.location.geolocation -> location.mailing_address.state_province_region -> location.country.currency_used", 
    "Rift Valley Province -> location.country.administrative_divisions -> location.country.currency",
    "Rift Valley Province -> location.administrative_division.country -> location.country.currency_used"
]
}
#
Question: The country with the National Anthem of Bolivia borders which nations?
Topic Entities:["National Anthem of Bolivia"],
Thought: There is only one topic entity, the answer is constrained by one path. 
For the path from "National Anthem of Bolivia", firstly, it should cover the country with the national athem "National Anthem of Bolivia". Second, it should cover the nations bordering that country.
Path: {
"National Anthem of Bolivia":[
    "National Anthem of Bolivia -> government.national_anthem_of_a_country.anthem -> location.country.national_anthem -> location.adjoining_relationship.adjoins", 
    "National Anthem of Bolivia -> location.country.national_anthem -> government.national_anthem_of_a_country.anthem -> location.location.adjoin_s -> location.adjoining_relationship.adjoins",
    "National Anthem of Bolivia -> location.country.national_anthem -> location.location.adjoin_s"
]
}
#

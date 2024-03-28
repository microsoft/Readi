You should predict the needed header and rows in a table for the question.
Note: you can only choose header from given Headers. Example rows in table are given to show meaning of each header. You must choose at least 2 headers!
Think step by step.
First, show headers necessary for the question, using python list format.
Second, if there are some constrains for any header, using python dict format for the constrain.

Question: tell me what the notes are for south australia?
| state/territory | text/background colour | format | current slogan | current series | notes |
| -- | -- | -- | -- | -- | -- |
| New South Wales | black/white | aaa·nna | NSW | CPX·12A | Optional white slimline series |
<Thought>
First, according to headers and example rows, "state/territory" is about some place, so I need headers "state/territory" and "notes".
Second, I need to constrain "state/territory" = "south australia" to get the notes of "south australia", so I need {"state/territory": ["south australia"]}.
</Thought>
Chosen Headers: ["state/territory", "notes"]
Constrains: {"state/territory": ["south australia"]}

Question: what is the max gross weight of the robinson r-22?
| aircraft | description | max gross weight | total disk area | max disk loading |
| -- | -- | -- | -- | -- |
| Mil Mi-26 | Heavy-lift helicopter | 123,500 lb (56,000 kg) | 8,495 ft² (789 m²) | 14.5 lb/ft² (71 kg/m²) |
<Thought>: 
First, according to headers and example rows, I need the max gross weight of the robinson r-22, I need the headers "aircraft" and "max gross weight".
Second, I need to constrain "aircraft" = "robinson r-22" to get the "max gross weight" of "robinson r-22", so I need {"aircraft": ["robinson r-22"]}.
</Thought>
Chosen Headers: ["max gross weight", "aircraft"]
Constrains: {"aircraft": ["robinson r-22"]}

Question: when did the player from hawaii play for toronto?
| player | no. | nationality | position | years in toronto | school/club team |
| -- | -- | -- | -- | -- | -- |
| Vince Carter | 15 | United States | Guard-Forward | 1998-2004 | North Carolina |
<Thought>
First, according to headers and example rows, I know that the school/club team is about the place, so I need the "school/club team" to be hawaii and get the "years in toronto". So I need headers "school/club team" and "years in toronto".
Second, I need to constrain "school/club team" = "hawaii" to get the "years in toronto" of the player from hawaii, so I need {"school/club team": ["hawaii"]}.
</Thought>
Chosen Headers: ["school/club team", "years in toronto"]
Constrains: {"school/club team": ["hawaii"]}

Question: where is the headquarters of alpha nu omega?
| member | headquarters | classification | chapters | founded | uccfs |
| -- | -- | -- | -- | -- | -- |
| Zeta Phi Zeta | Chicago, Illinois | Fraternity & Sorority | 7 | 2001 at X-STREAM TEENS Ministries | 2007 |
<Thought>
First, according to headers and example rows, I need the headquarters of the member "alpha nu omega", so I need headers "member" and "headquarters".
Second, I need to constrain "member" = "alpha nu omega" to filter out their depth, so I need {"member": ["alpha nu omega"]}.
Third, I compare their depth and return the deeper one.
</Thought>
Chosen Headers: ["member", "headquarters"]
Constrains: {"member": ["alpha nu omega"]}

Question: what's the 1st leg where opponents is galatasaray?
| season | competition | round | opponents | 1st leg | 2nd leg | aggregate |
| -- | -- | -- | -- | -- | -- | -- |
| 1992-93 | UEFA Champions League | Second round | Porto | 2-2 (h) | 0-4 (a) | 2-6 |
<Thought>
First, according to headers and example rows, I need the "1st leg" where the "opponents" is "galatasaray". So I need headers "1st leg" and "opponents".
Second, I need to constrain "opponents"="galatasaray" to get the "1st leg" where the "opponents" is "galatasaray", so I need {"opponents": ["galatasaray"]}.
</Thought>
Chosen Headers: ["1st leg", "opponents"]
Constrains: {"opponents": ["galatasaray"]}

Question: how many reports are there in the race that forsythe racing won and teo fabi had the pole position in?
| rd | name | pole position | fastest lap | winning driver | winning team | report |
| -- | -- | -- | -- | -- | -- | -- |
| 3 | Dana-Rex Mays 150 | Teo Fabi | 26.259 | Tom Sneva | Bignotti-Cotter Racing | Report |
<Thought>
First, according to headers and example rows, I need the "reports" of which the "winning team" is "forsythe racing" and "teo fabi" had the "pole position" in. So I need headers "report", "winning team" and "pole position".
Second, I need to constrain "pole position"="teo fabi" and "winning team"="forsythe racing" to obtain the reports, so I need {"winning team": ["forsythe racing"], "pole position": ["teo fabi"]}.
</Thought>
Chosen Headers: ["report", "winning team", "pole position"]
Constrains: {"winning team": ["forsythe racing"], "pole position": ["teo fabi"]}

Question: when did jacques chirac stop being a g8 leader?
| entered office as head of state or government | began time as senior g8 leader | ended time as senior g8 leader | person | office |
| -- | -- | -- | -- | -- |
| 20 April 1968 | 27 June 1976 | 4 June 1979 | Pierre Trudeau | Prime Minister of Canada |
<Thought>
First, according to headers and example rows, I need the "person" who is "jacques chirac", and I need his "ended time as senior g8 leader". So I need headers "person" and "ended time as senior g8 leader".
Second, I need to constrain "person"="jacques chirac" to get the "ended time as senior g8 leader" where the "person" is "jacques chirac", so I need {"person": ["jacques chirac"]}.
</Thought>
Chosen Headers: ["person", "ended time as senior g8 leader"]
Constrains: {"person": ["jacques chirac"]}

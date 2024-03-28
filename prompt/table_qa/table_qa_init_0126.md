You should predict the needed header and rows in a table for the question.
Note: you can only choose header from given Headers. Example rows in table are given to show meaning of each header. You must choose at least 2 headers!
Think step by step.
First, show headers necessary for the question, using python list format.
Second, if there are some constrains for any header, using python dict format for the constrain.

Question: what was the last year where this team was a part of the usl a-league?
| year | division | league | regular season | playoffs | open cup | avg. attendance |
| -- | -- | -- | -- | -- | -- | -- |
| 2001 | 2 | USL A-League | 4th, Western | Quarterfinals | Did not qualify | 7,169 |
<Thought>
First, according to headers and example rows, I need the years the team is in usl a-league league and return the latest year, so I need headers "year" and "league".
Second, I need to constrain "league" = "usl a-league", so I need {"league": ["usl a-league"]}.
Third, I calculate the latest "Year".
</Thought>
Chosen Headers: ["year", "league"]
Constrains: {"league": ["usl a-league"]}

Question: how many people stayed at least 3 years in office?
| | name | took office | left office | party |
| -- | -- | -- | -- | -- |
| 11 | William McCreery | March 4, 1803 | March 3, 1809 | Democratic Republican |
<Thought>: 
First, according to headers and example rows, I need the stayed time for each person, I need the "took office" and "left office" to calculate it, so I need headers "took office" and "left Office".
Second, I calculate "left Office" - "took office" to know the stayed years and then count the number, so I need no other constrain.
</Thought>
Chosen Headers: ["took office", "left office"]
Constrains: {}

Question: who was the opponent in the first game of the season?
| date | opponent | venue | result | attendance | scorers |
| -- | -- | -- | -- | -- | -- |
| 15 August 1987 | Derby County | Away | 0–1| 17,204 | — |
<Thought>
First, according to headers and example rows, I need the time of the game to know the first time, and opponent of that game, so I need headers "date" and "opponent".
Second, I calculate the first game and get the opponent, so I need no other constrain.
</Thought>
Chosen Headers: ["date", "opponent"]
Constrains: {}

Question: which is deeper, lake tuz or lake palas tuzla?
| name in english | name in turkish | area (km2) | depth | location (districts and/or provinces) |
| -- | -- | -- | -- | -- |
| Lake Van | Van Gölü | 3755 km2 | 451 m | Van, Bitlis |
<Thought>
First, according to headers and example rows, I need the depth for the two lakes, so I need headers "name in english" and "depth".
Second, I need to constrain "name in english" = "lake tuz" and "lake palas tuzla" to filter out their depth, so I need {"name in english": ["lake tuz", "lake palas tuzla"]}.
Third, I compare their depth and return the deeper one.
</Thought>
Chosen Headers: ["name in english", "depth"]
Constrains: {"name in english": ["lake tuz", "lake palas tuzla"]}

Question: which ship in auckland had the fastest speed in knots?
| name | dates | grt | propulsion | port | notes |
| -- | -- | -- | -- | -- | -- |
| Arataki  i | 1948-84 | 74 | 320 bhp diesel, 10 knots (19 km/h) |  | US Navy harbour tug |
<Thought>
First, according to headers and example rows, I need the ship which is in auckland and has the fastest speed in knots, and I can tell that the header "propulsion" is about the speed. So I need headers "name", "propulsion" and "port".
Second, I need to constrain "port"="auckland", so I need {"port"=["auckland"]}.
Third, I need to calculate the ship with the highest "propulsion" and return its "name".
</Thought>
Chosen Headers: ["port", "propulsion", "name"]
Constrains: {"port"=["auckland"]}

Question: what is the difference between the number of employees at mundelein elementary school district 75 and fremon school district 79?
| # | employer | # of employees |
| -- | -- | -- |
| 2 | Mundelein Park District | 422 |
<Thought>
First, according to headers and example rows, I need the number of employees at to different districs, and I can tell that the header "employer" is about the district. So I need headers "employer" and "# of employees".
Second, I need to constrain "employer" = "mundelein elementary school district 75" and "fremon school district 79" to filter out their number of employees, so I need {"employer": ["mundelein elementary school district 75", "fremon school district 79"]}.
Third, I calculate the "# of employees" for "mundelein elementary school district 75" - "# of employees" for "fremon school district 79" to get the difference.
</Thought>
Chosen Headers: ["employer", "# of employees"]
Constrains: {"employer": ["mundelein elementary school district 75", "fremon school district 79"]}


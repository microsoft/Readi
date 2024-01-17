You should predict reasoning path of the question.
Candidate relations are as follows: actor_to_movie, movie_to_writer, tag_to_movie, writer_to_movie, movie_to_year, director_to_movie, movie_to_language, movie_to_genre, movie_to_director, movie_to_actor, movie_to_tags
Note: if you need to get the type of the movie, use movie_to_genre.
Think step by step.
Give the logical form of your reasoning path, [ENTITY] represents starting entity.
Finally, present your relations in python list format.

Question: which person wrote the films directed by [Yuriy Norshteyn]
<Thought>
First, I need to know the films directed by [Yuriy Norshteyn], he is a director, so I need a relation from director to movie. That is director_to_movie relation.
Second, I need to know the writer of the movie, so I need a relation from movie to writer. That is movie_to_writer.
</Thought>
Logical Form: [Yuriy Norshteyn] -> director_to_movie -> movie_to_writer
Relations: ["director_to_movie", "movie_to_writer"]

Question: which movies have the same director of [Just Cause]
<Thought>:
First, I need to know the director of the movie [Just Cause], it is a movie, so I need a relation from movie to director. That is movie_to_director.
Second, I need to know movies directed by the director, so I need a relation from director to movie. That is director_to_movie.
</Thought>
Logical Form: [Just Cause] -> movie_to_director  -> director_to_movie
Relations: ["movie_to_director", "director_to_movie"]

Question: what genres do the movies written by [Maureen Medved]
<Thought>
First, I need to know the movies written by [Maureen Medved], he is a writer, so I need a relation from movie to writer. That is movie_to_writer.
Second, I need to know the genres of the movies, so I need a relation from movie to genre. That is movie_to_genre.
</Thought>
Logical Form: [Maureen Medved] -> writer_to_movie -> movie_to_genre
Relations: ["writer_to_movie", "movie_to_genre"]

Question: what were the release years of the movies acted by [Todd Field]
<Thought>
First, I need to know the movies acted by [Todd Field], she is an actor, so I need a relation from actor to movie. That is actor_to_movie.
Second, I need to know the release years of the movies, so I need a relation from movie to release year. That is movie_to_year.
</Thought>
Logical Form: [Todd Field] -> actor_to_movie -> movie_to_year
Relations: ["actor_to_movie", "movie_to_year"]

Question: the films written by [Babaloo Mandel] starred which actors
<Thought>
First, I need to know the films written by [Babaloo Mandel], he is a writer, so I need a relation from writer to movie. That is writer_to_movie.
Second, I need to know the actor starred in the films, so I need a relation from movie to actor. That is movie_to_actor.
</Thought>
Logical Form: [Babaloo Mandel] -> writer_to_movie -> movie_to_actor
Relations: ["writer_to_movie", "movie_to_actor"]
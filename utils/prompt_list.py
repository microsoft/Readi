refine_prompt="""Now you are a plan refiner on a knowledge graph. Your goal is to refine the partially grounded relation path from a topic entity to reach the answer, according to some given information, to make the plan more faithful to the knowledge graph.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the most relevant knowledge to answer the question, so the relation paths are from topic entities to the answer according to such question.
2. Initial Path: an initial ungrounded relation path. The format is dict, the key of which is the starting topic entities and the value of which is an array of relations (partially grounded) to reach the answer of the Question.
3. Grounded Knowledge: some already-grounded knowledge from one of the topic entities, according to the Question and Initial Path. The format is a 2-dimensional array. Each array inside, is a grounded path of triple patterns grounded in the knowledge graph, based on parts of the Initial Plans.
4. Candidate Relations: some possible candidate relations linked to some grounded nodes in Grounded Knowledge. The format is a dict, the key of which is some grounded entities (intermediate entities in the Grounded Knowledge, or just the topic entity), the value of which is relations connected to this entity (If Grounded Knowledge is [[]], relations to the topic entity will be given). This information is given because some relations in the Initial Plan cannot be grounded around the entities, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. Your Refined Path must be in a json dict format, just the same format as the input Initial Path. The key are topic entities. And the value of the output dict is the Refined or remained array of relations.
2. Topic entities are given, the output dict must include all the topic entities as the Initial Path. You should just refine ONE path in the value of the dict, based on Grounded Knowledge and Candidate Relations. Other parts should remain the same as the Initial Plan. 
3. Each topic entity must have a path the reach the answer. In other words, if a Question has multiple topic entities, the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities
4. Grounded Knowledge is obtained by grounding the given initial plan relation-by-relation from a topic entity. However, some relations cannot be grounded according to the plan, which means the path in the Initial Plan is unfaithful from this relation. You should refine the unfaithful part of the path, so I can ground the Refined Path to the knowledge graph smoothly.
5. According to rule RULE 4, some parts of the Initial Path can be faithful (able to be grounded to the knowledge base). However, this does not mean that the refined one must include the grounded part. Think golbally of the question, though some part is correct locally, it does not mean this part is the golden optimal from the topic entity to the answer.
6. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes(blank nodes) on Freebase. These nodes can not be the answer, so you must step forward according to Candidate Relations, or change the previous relation refine the original path.

Here are some practical tips for you to refine the plan (just some advice, you donnot have to choose only from these):
1. Identify the topic entities from the key of Initial Path. This is easy, every key in the dict is one topic entity. And then, Note that Grounded Knowledge and Candidate Relations are just information obtained by grounding ONE particular path (from one topic entity). So you should identify the ONE path and refine it, other path should remain the same(According to RULE 2).
2. If the Grounded Knowledge is already sufficient to answer the question, this means maybe the ONE path is too long. Refine it according to the Question and the Grounded Knowledge.
3. If the Grounded Knowledge is not sufficient, and some part of the path is not grounded, this means something in the ONE path is unfaithful. So choose a relation in Candidate Relations and refine the plan (you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. If the Grounded Knowledge is empty or is [[]], this means no relations ine the ONE path starting from the topic entity is grounded. So you should choose the most relevant relation from the Candidate Relations of the topic entity to refine the whole path.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Initial Path: {
"United Kingdom": ["location.location.religions"],
"St. Mary's Cathedral, Batticaloa": ["religion.religion.places_of_worship"]
}
Grounded Knowledge: [[('United Kingdom','location.statistical_region.religions', 'm.047hrrd'),('United Kingdom','location.statistical_region.religions', 'm.043trcf'),('United Kingdom','location.statistical_region.religions', 'm.047hrrr'),('United Kingdom','location.statistical_region.religions', 'm.047hrqc'),('United Kingdom','location.statistical_region.religions', 'm.047hrr4'),('United Kingdom','location.statistical_region.religions', 'm.047hrr_'),('United Kingdom','location.statistical_region.religions', 'm.047hrs7'),('United Kingdom','location.statistical_region.religions', 'm.047hrsh')]]
Candidate Relations:{
'm.047hrrd': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.043trcf': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrrr': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrqc': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr4': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr_': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrs7': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrsh': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
}
Thought: According to the key of Initial Plan, there are two topic entities, "United Kingdom" and "St. Mary's Cathedral, Batticaloa", so the answer is constrained by two paths. Based on Grounded Knowledge and Candidate Relations, I should refine the path starting from "United Kingdom". Based on the Question, I this path should constrain the answer to be the major religion in the UK. The Grounded Knowledge is not enough to answer this and it seems they reach some cvt nodes (blank nodes) on Freebase knowledge base. Fortunately, based on Candidate Relations, I can add a relation 'location.religion_percentage.religion' to current path, and refine the relations to the faithful ones in the knowledge graph, the Refined Path is as follows.
Refined Path:{
"United Kingdom":["location.statistical_region.religions","location.religion_percentage.religion"],
"St. Mary's Cathedral, Batticaloa": ["religion.religion.places_of_worship"]
}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?
Initial Path:{
"Rift Valley Province":["place.administrative_division.country","location.location.geolocation","location.mailing_address.state_province_region","place.country.currency_used"]
}
Grounded Knowledge: [[('Rift Valley Province', 'location.administrative_division.country', 'Kenya'), ('Kenya', 'location.country.currency_used', 'Kenyan shilling')],[('Rift Valley Province', 'location.location.geolocation', 'm.02_pgyk'), ('m.02_pgyk', 'location.mailing_address.state_province_region', 'Rift Valley Province')],[('Rift Valley Province', 'location.mailing_address.state_province_region', 'Rift Valley Province')]]
Candidate Relations:{
'Rift Valley': ['base.aareas.schema.administrative_area.administrative_area_type', 'base.aareas.schema.administrative_area.administrative_parent', 'base.schemastaging.context_name.pronunciation', 'kg.object_profile.prominent_type', 'location.administrative_division.country', 'location.administrative_division.fips_10_4_region_code', 'location.location.area', 'location.location.containedby', 'location.location.containedby', 'location.location.contains', 'location.location.contains', 'location.location.geolocation', 'location.location.geometry'],
'm.02_pgyk': ['location.geocode.latitude', 'location.geocode.longitude','location.location.geolocation', 'type.type.instance']
}
Thought: According to the key of Initial Path, there is one topic entity, "Rift Valley Province", so the answer is constrained by one path. According to a path [('Rift Valley Province', 'location.administrative_division.country', 'Kenya'), ('Kenya', 'location.country.currency_used', 'Kenyan shilling')] in Grounded Knowledge, I find that firstly Rift Valley Province is located in Kenya. Secondly,the currency used in Kenya is Kenyan shilling. So the Grounded Knowledge is sufficienct to answer the Question. And I can refine the relations in the Initial Path to the faithful ones in the knowledge graph, the Refined Path is as follows.
Refined Path:{
"Rift Valley Province":["location.administrative_division.country","location.country.currency_used"]
}
#
"""


refine_prompt_path="""Now you are a plan refiner on a knowledge graph. Your goal is to refine the partially grounded relation path from a topic entity to reach the answer, according to some given information, to make the plan more faithful to the knowledge graph.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the most relevant knowledge to answer the question, so the relation paths are from topic entities to the answer according to such question.
2. Initial Path: an initial ungrounded relation path. The format is dict, the key of which is the starting topic entities and the value of which is a path from the topic entity to reach the answer of the Question. Note that the path here is some relations connected by "->", and the starting point of the path is the topic entity.
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C throught relation B, the starting point is the topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some part of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the intermediate entity. The format is a dict, the key of which is some intermediate entities (or just the topic entity), the value of which is relations connected to the entity. Usually, the entities in this dict is the end point in some paths in Grounded Knowledge, following which the relations in Initial Plan cannot be grounded. Or if the Grounded knowledge is empty, I will show you relations of topic entities. This information is given because some relations in the Initial Plan cannot be grounded around the entities, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. Most important! Your Refined Path must be in a json dict format, just the same format as the input Initial Path. The key is topic entities. And the value is the Refined or remained relation paths.
2. Topic entities are given, the output dict must include all the topic entities as the Initial Path. To make sure you do a good job, you should just refine ONE path at a time. Other parts should remain the same as the Initial Plan. 
3. Each topic entity must have a path the reach the answer. In other words, if a Question has multiple topic entities, the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities.
4. Grounded Knowledge is obtained by grounding the given initial plan relation-by-relation from a topic entity. However, some relations cannot be grounded according to the plan, which means the path in the Initial Plan is unfaithful from this relation. You should refine the unfaithful part of the path, so I can ground the Refined Path to the knowledge graph smoothly.
5. According to rule RULE 4, some parts of the Initial Path can be faithful (able to be grounded to the knowledge base). However, this does not mean that the refined one must include the grounded part. Think globally of the question, though some part is correct locally, it does not mean this part is the golden optimal from the topic entity to the answer.
6. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes(blank nodes) on Freebase. These nodes can not be the answer, so you must step forward according to Candidate Relations, or change the previous relation refine the original path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Error Location: Identify the topic entities from the key of Initial Path. This is easy, every key in the dict is one topic entity. And then, Note that Candidate Relations, obtained by grounding one particular plan, is relevant to just ONE particular path in Initial Plan, so you should identify the ONE path and refine it, other paths should remain the same(According to RULE 2).
2. Sufficiency: If the Grounded Knowledge is already sufficient to answer the question, this means maybe the ONE path is too long. Just refine the path by cutting some relations according to the Question and the Grounded Knowledge.
3. Faithfulness: If the Grounded Knowledge is not sufficient (some part of the path is not grounded), this means something in the ONE path is unfaithful. So choose a relation in Candidate Relations and reconsider the rest of the plan (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty or is [[]], or a relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should first choose the most relevant relation from the Candidate Relations of the topic entity, and reconstruct the whole plan in order to get the answer.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Initial Path: {
"United Kingdom": "United Kingdom -> location.location.religions",
"St. Mary's Cathedral, Batticaloa": "St. Mary's Cathedral, Batticaloa -> religion.religion.places_of_worship"
}
Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_
Candidate Relations:{
'm.047hrrd': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.043trcf': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrrr': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrqc': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr4': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr_': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
}
Thought: First, the key of Initial Plan is ["United Kingdom","St. Mary's Cathedral, Batticaloa"], so there are two topic entities (2 keys in dict) and the answer is constrained by two paths. 
Second, based on Grounded Knowledge and Candidate Relations, I should refine the path starting from "United Kingdom" to reach the answer. Based on the Question, this path should cover the major religion in United Kingdom. 
Third, Grounded Knowledge is not sufficient to answer this, they just reach the religions but cannot tell the major one and some knowledeg reaches some cvt nodes (blank nodes). 
Fourth, based on Candidate Relations, I need to choose a relation to get the major religions, so I choose 'location.religion_percentage.religion' and add it to current path, and refine the relations to the faithful ones in the knowledge graph, the Refined Path is as follow.
Lastly, other paths remain the same as in the Initial Path.
Refined Path:{
"United Kingdom":"United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion",
"St. Mary's Cathedral, Batticaloa": "St. Mary's Cathedral, Batticaloa -> religion.religion.places_of_worship"
}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?
Initial Path:{
"Rift Valley Province": "Rift Valley Province -> place.administrative_division.country -> location.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used"
}
Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.country.currency_used -> Kenyan shilling
Rift Valley Province -> location.location.geolocation -> m.02_pgyk -> location.mailing_address.state_province_region -> Rift Valley Province
Rift Valley Province -> location.mailing_address.state_province_region -> Rift Valley Province
Candidate Relations:{
'Rift Valley Province': ['base.aareas.schema.administrative_area.administrative_area_type', 'base.aareas.schema.administrative_area.administrative_parent', 'base.schemastaging.context_name.pronunciation', 'kg.object_profile.prominent_type', 'location.administrative_division.country', 'location.administrative_division.fips_10_4_region_code', 'location.location.area', 'location.location.containedby', 'location.location.containedby', 'location.location.contains', 'location.location.contains', 'location.location.geolocation', 'location.location.geometry'],
}
Thought: First, the key of Initial Path is ["Rift Valley Province"], so there is one topic entity and the answer is constrained by one path.
Second, according to a path "Rift Valley Province -> location.administrative_division.country -> Kenya -> location.country.currency_used -> Kenyan shilling" in Grounded Knowledge, I find that, firstly, Rift Valley Province is located in Kenya. Secondly,the currency used in Kenya is Kenyan shilling. So the Grounded Knowledge is sufficienct to answer the Question. And I can refine the relations in the Initial Path to the faithful ones in the knowledge graph, the Refined Path is as follow.
Refined Path:{"Rift Valley Province":"Rift Valley Province -> location.administrative_division.country -> location.country.currency_used"}
#
"""


refine_prompt_path_one_path = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is dict, the key of which is a starting topic entity and the value of which is a path from the topic entity to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. The format is a dict, the key of which is some intermediate entities (or just the topic entity), the value of which is relations connected to the entity. Usually, entities in this dict is the end point in some paths in Grounded Knowledge, following which the relations in Initial Plan cannot be grounded. Or if the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This information is because relations in the Initial Plan cannot be grounded from the begining, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. Most important! Your Refined Path must be in a json dict format, just the same format as the input Initial Path. The key is topic entities. And the value is the Refined relation paths. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
2. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan, I will do the rest.
3. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes(blank nodes) on Freebase. These nodes can not be the answer, so you must step forward according to Candidate Relations, or change the previous relation to refine the path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity, yes, this is so important), based on the Question. After this, you should check if the Grounded Knowledeg meets your expectations. If not, location the unfaithful part, and refine the path to reach the answer.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, this means maybe the ONE path is too long. Just refine the path by cutting some relations according to the Question and the Grounded Knowledge.
3. Faithfulness: If the Grounded Knowledge is not sufficient (some part of the path is not grounded) or some knowledge is irrelevant to this path, this means something in the path is unfaithful. So choose a relation in Candidate Relations and reconsider the rest of the plan (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty or is [[]], or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should first choose the most relevant relation from the Candidate Relations of the topic entity, and reconstruct the whole plan in order to get the answer.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Initial Path: {
"United Kingdom": "United Kingdom -> location.location.religions -> location.location.marjor_religions"
}
Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_
Candidate Relations:{
'm.047hrrd': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.043trcf': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrrr': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrqc': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr4': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr_': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
}
Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom" to reach the answer (expectation). 
Based on Grounded Knowledge and Candidate Relations, Grounded Knowledge is not sufficient to meet expectations, they just reach the religions but cannot tell the major one. And some knowledeg reaches some cvt nodes (blank nodes). So this is insufficient, I need to choose a relation to get the major religions.
Based on Candidate Relations, I choose 'location.religion_percentage.religion' and add it to current path, and refine the relations to the faithful ones in the knowledge graph, the Refined Path is as follow.
Refined Path:{"United Kingdom":"United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion"}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?
Initial Path:{
"Rift Valley Province": "Rift Valley Province -> place.administrative_division.country -> location.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used"
}
Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.country.currency_used -> Kenyan shilling
Rift Valley Province -> location.location.geolocation -> m.02_pgyk -> location.mailing_address.state_province_region -> Rift Valley Province
Rift Valley Province -> location.mailing_address.state_province_region -> Rift Valley Province
Candidate Relations:{
'Rift Valley Province': ['base.areas.schema.administrative_area.administrative_area_type', 'base.aareas.schema.administrative_area.administrative_parent', 'base.schemastaging.context_name.pronunciation', 'kg.object_profile.prominent_type', 'location.administrative_division.country', 'location.administrative_division.fips_10_4_region_code', 'location.location.area', 'location.location.containedby', 'location.location.containedby', 'location.location.contains', 'location.location.contains', 'location.location.geolocation', 'location.location.geometry'],
}
Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, this path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
According to a path "Rift Valley Province -> location.administrative_division.country -> Kenya -> location.country.currency_used -> Kenyan shilling" in Grounded Knowledge, I find that, firstly, Rift Valley Province is located in Kenya. Secondly,the currency used in Kenya is Kenyan shilling. So the Grounded Knowledge is sufficienct to reach the answer (meet my expectations). And I can refine the relations in the Initial Path to the faithful ones in the knowledge graph, the Refined Path is as follow.
Refined Path:{"Rift Valley Province":"Rift Valley Province -> location.administrative_division.country -> location.country.currency_used"}
#
"""


refine_prompt_path_one_path_1222 = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is dict, the key of which is a starting topic entity and the value of which is a path from the topic entity to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. The format is a dict, the key of which is some intermediate entities (or just the topic entity), the value of which is relations connected to the entity. Usually, entities in this dict is the end point in some paths in Grounded Knowledge, following which the relations in Initial Plan cannot be grounded. If the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This information is given because relations in the Initial Plan cannot be grounded, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. Most important! Your Refined Path must be in a json dict format, just the same format as the input Initial Path. The key is topic entities. The value is the Refined relation paths. Note that the path here is some relations connected by "->", and just the start point of the path is the topic entity. There is no other entity in this path!
2. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan, I will do the rest.
3. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes(blank nodes) on Freebase. These nodes can not be the answer, so you must step forward according to Candidate Relations, or change the previous relation to refine the path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity), based on the Question. After this, you should check if the Grounded Knowledeg meets your expectations. If not, locate the unfaithful part, and refine the path to reach the answer.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, this means maybe the ONE path is too long. Just refine the path by cutting some relations according to the Question and the Grounded Knowledge.
3. Faithfulness: If the Grounded Knowledge is not sufficient (some part of the path is not grounded) or some knowledge is irrelevant to this path, this means something in the path is unfaithful. So choose a relation in Candidate Relations and reconsider the rest of the plan (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty or is [[]], or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should first choose the most relevant relation from the Candidate Relations of the topic entity, and reconstruct the whole plan in order to get the answer.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?

Initial Path: {
"United Kingdom": "United Kingdom -> location.location.religions -> location.location.marjor_religions"
}

Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_

Candidate Relations:{
'm.047hrrd': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.043trcf': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrrr': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrqc': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr4': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
'm.047hrr_': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
}

Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom" to reach the answer (expectation).
In Grounded Knowledge, the relation "location.location.religions" is grounded to "location.statistical_region.religions", but the entities seem some cvt nodes (starting with "m." or "g.") . So I cannot tell if the knowledge are faithful by now. However, from the Gounded Knowledge the major religion is not known (not meeting the expectation). According to Candidate Relations, the relation "location.religion_percentage.religion" is relevant to obtain major religions,  I can add it to current path, so that the path may meet my expectation. And I refine the relation 'location.location.religions' to the grounded relation "location.statistical_region.religions".
The Refined Path is as follow.

Refined Path:{"United Kingdom":"United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion"}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?

Initial Path:{"Rift Valley Province": "Rift Valley Province -> place.administrative_division.country -> place.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used"}

Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.location.geolocation -> m.046vy0w

Candidate Relations:{'m.046vy0w': ['type.object.type','location.geocode.latitude,'location.geocode.longitude']}

Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, the path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
In the Grounded Knowledge, the relation "location.administrative_division.country" is grounded to "location.administrative_division.country", and the relation "location.location.geolocation" is grounded to "location.location.geolocation".
I find that, firstly, Rift Valley Province is connected to Kenya through relation "location.administrative_division.country". which means Rift Valley Province is located in the naton Kenya, This is faithful and meets part of my expectation. So I can refine the "location.administrative_division.country" to "location.administrative_division.country".
Secondly, Kenya is connected to a cvt node "m.046vy0w" through the relation "location.location.geolocation". And Candidate Relations gives some relations around the cvt node. However, I need to know the currency used in Kenya to meet my expectation. I cannot find some relevant relation and the grounded relation "location.location.geolocation" seems irrelevant to the path. So the relation "location.location.geolocation" is unfaithful, and relations connected to kenya are not known. So I should refine it to on my own to get the currency of Kenya.
The Refined Path is as follow.

Refined Path:{"Rift Valley Province":"Rift Valley Province -> location.administrative_division.country -> location.country.currency_used"}
#
"""


refine_prompt_path_one_path_1224 = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is a string, which is a path from the topic entity, connecting some relations to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. If the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This is given because some relations in the Initial Plan cannot be grounded (unfaithful), so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. Most important! Your Refined Path must be in a string format starting from the topic entity, just the same format as the input Initial Path. Note that the path here is some relations connected by "->", and just the start point of the path is the topic entity. There is no other entities in this path!
2. You MUST NOT change the topic entity, which means the starting point of the Initial Plan and the Refined Plan must be exactly the same!
3. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, this means the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan.
4. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes (blank nodes) on Freebase knowledge base. These nodes can not be the answer, so if they are the end of path you must step forward according to Candidate Relations, or refine the previous path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity), based on the Question. After this, you should check if the Grounded Knowledeg meets your expectations. If not, locate the unfaithful part, and refine the path.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, already meeting your expectation (reach the answer), just refine the relations in the Initial Path to the grounded ones. If there are still some relations ungrounded in Initial Plan, and Candididate Relations are given, this means the Initial Plan maybe is too long, just cut it.
3. Faithfulness: If some knowledge in Grounded Knowledge is irrelevant to this path, this means something in the path is unfaithful. Refine the plan to give a faithful one. If some knowledge meets parts of your expectation, and some relations are not grounded, choose a relation in Candidate Relations (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty or is [[]], or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should choose a relevant relation from the Candidate Relations of the topic entity, and reconstruct the whole plan in order to get the answer.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?

Initial Path: United Kingdom -> location.location.religions -> location.location.marjor_religions

Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_

Candidate Relations: ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']

Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom" to reach the answer (expectation).
In Grounded Knowledge, the relation "location.location.religions" is grounded to "location.statistical_region.religions", but the entities seem some cvt nodes (starting with "m." or "g.") . So I cannot tell if the knowledge is faithful by now. However, from the Gounded Knowledge the major religion is not known (not meeting the expectation). According to Candidate Relations, the relation "location.religion_percentage.religion" is relevant to obtain major religions,  I can add it to current path, so that the path may meet my expectation. And I refine the relation 'location.location.religions' to the grounded relation "location.statistical_region.religions".
The Refined Path is as follow.

Refined Path: United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion
#
Question: Rift Valley Province is located in a nation that uses which form of currency?

Initial Path: Rift Valley Province -> place.administrative_division.country -> place.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used

Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.location.geolocation -> m.046vy0w

Candidate Relations:['type.object.type','location.geocode.latitude,'location.geocode.longitude']

Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, the path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
In the Grounded Knowledge, the relation "location.administrative_division.country" is grounded to "location.administrative_division.country", and the relation "location.location.geolocation" is grounded to "location.location.geolocation".
I find that, firstly, Rift Valley Province is connected to Kenya through relation "location.administrative_division.country". which means Rift Valley Province is located in the nation Kenya, this is faithful and meets part of my expectation. So I can refine the "location.administrative_division.country" to "location.administrative_division.country".
Secondly, Kenya is connected to a cvt node "m.046vy0w" through the relation "location.location.geolocation", which reaches a cvt node and some Candidate Relations around this cvt node is given, and they seems just about some geological information, with nothing about the currency. However, I need to know the currency used in Kenya to meet my expectation. I cannot find some relevant relation and the grounded relation "location.location.geolocation" seems irrelevant to the path. So the relation "location.location.geolocation" is unfaithful. So I should refine it to on my own to get the currency of Kenya.
The Refined Path is as follow.

Refined Path: Rift Valley Province -> location.administrative_division.country -> location.country.currency_used
#
"""


refine_prompt_path_one_path_add_stop_condition_1225 = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is a string, which is a path from the topic entity, connecting some relations to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. If the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This is given because some relations in the Initial Plan cannot be grounded, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. If Grounded Knowledge is sufficient to answer the question, or if it meets your expectations of the path, output ***STOP REFINE*** in the last line! If not, output Refine Path according to RULE 2.
2. Important! Your Refined Path must be in a string format starting from the topic entity, just the same format as the input Initial Path. Note that the path here is some relations connected by "->", and just the start point of the path is the topic entity. There is no other entities in this path!
3. You MUST NOT change the topic entity, which means the starting point of the Initial Plan and the Refined Plan must be exactly the same!
4. If the Candidate Relations is [] or empty, this means the Initial Path is fully grounded. If the Gounded Knowledge meets your expectation (contain necessary information to find the answer), you can just output ***STOP REFINE***. But if the Grounded Knowledge does not meet your expectation, this means the Initial Path has some parts irrelevant to the question. So refine the path on your own!
5. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, which means the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan.
6. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes (blank nodes) on Freebase knowledge base. These nodes can not be the answer, so if they are the end of path you must step forward according to Candidate Relations, or refine the previous path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity), based on the Question. After this, you should check if the Grounded Knowledge meets your expectations. If not, locate the irrelevant part, and refine the path.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, already meeting your expectation (reach the answer), just refine the relations in the Initial Path to the grounded ones. If there are still some relations ungrounded in Initial Plan, and Candididate Relations are given, this means the Initial Plan maybe is too long, just cut it.
3. Faithfulness: If some knowledge in Grounded Knowledge is irrelevant to this path, this means something in the Initial Path is unfaithful. Refine the plan. If some knowledge meets parts of your expectation, and some relations are not grounded, choose a relation in Candidate Relations (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty or is [[]], or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should choose a relevant relation from the Candidate Relations of the topic entity, and reconstruct the whole plan in order to get the answer.

Let me show you some examples.
# Question: The movie featured Miley Cyrus and was produced by Tobin Armbrust?

Initial Path: Miley Cyrus -> film.film.actor -> film.film.performance

Grounded Knowledge: Miley Cyrus -> film.actor.film -> m.010tw6z6 -> film.performance.film -> Wizards on Deck with Hannah Montana
Miley Cyrus -> film.actor.film -> m.0h0_35j -> film.performance.film -> The World According to Miley Cyrus
Miley Cyrus -> film.actor.film -> m.04g4mbv -> film.performance.film -> Bolt
Miley Cyrus -> film.actor.film -> m.0gvn_qx -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.0w2y18w -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.07ykl5g -> film.performance.film -> The Last Song
Miley Cyrus -> film.actor.film -> m.0vpd23v -> film.performance.film -> Hannah Montana and Miley Cyrus: Best of Both Worlds Concert
Miley Cyrus -> film.actor.film -> m.08c_hc1 -> film.performance.film -> Super Rhino
Miley Cyrus -> film.actor.film -> m.04g4mcc -> film.performance.film -> Big Fish
Miley Cyrus -> film.actor.film -> m.08cvslc -> film.performance.film -> Sonic the Hedgehog
Miley Cyrus -> film.actor.film -> m.0dls5z5 -> film.performance.film -> LOL

Candidate Relations: ['dataworld.gardening_hint.last_referenced_by', 'dataworld.gardening_hint.replaced_by', 'film.director.film', 'film.film.country', 'film.film.directed_by', 'film.film.genre', 'film.film.initial_release_date', 'film.film.language', 'film.film.prequel', 'film.film.release_date_s', 'film.film.runtime', 'film.film.sequel', 'film.film.starring', 'film.film.written_by', 'film.film_cut.film', 'film.film_genre.films_in_this_genre', 'film.film_regional_release_date.film', 'film.performance.film', 'film.writer.film', 'imdb.topic.title_id', 'kg.object_profile.prominent_type', 'tv.tv_director.episodes_directed', 'tv.tv_program.episodes', 'tv.tv_series_episode.air_date', 'tv.tv_series_episode.director', 'tv.tv_series_episode.episode_number', 'tv.tv_series_episode.next_episode', 'tv.tv_series_episode.season', 'tv.tv_series_episode.season_number', 'tv.tv_series_episode.series', 'tv.tv_series_episode.writer']

Thought: According to the initial path, this path starts from "Miley Cyrus". Based on the Question, the path should cover the film acted by Miley Cyrus, to reach the answer (expectation).
In the Grounded Knowledge, the relation "film.film.actor" is grounded to "film.actor.film", and the relation "film.film.performance" is grounded to "film.performance.film".
I find that, firstly, Miley Cyrus is connected to some cvt nodes (starting with "m."), through "film.actor.film", which are some intermediate nodes.
Secondly, the cvt nodes are connected to "film.performance.film", and we obatin some films performed by Miley Cyrus. Now I know the films acted by Miley Cyrus.
So this whole path is grounded and meets my expectation. 
So I think we donnot need to further refine the path to get more information.

***STOP REFINE***
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?

Initial Path: United Kingdom -> location.location.religions -> place.religion.major_religions

Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_
United Kingdom -> location.location.contains -> Heaton railway station
United Kingdom -> location.location.contains -> Bakersfield, Nottingham
United Kingdom -> location.location.contains -> Knockloughrim
United Kingdom -> location.location.contains -> Oakenshaw

Candidate Relations: ['location.location.containedby', 'location.location.geolocation', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion', 'type.object.type']

Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom" to reach the answer (expectation).
In Grounded Knowledge, the relation "location.location.religions" is grounded to "location.statistical_region.religions".
Firstly, United Kingdom is connected to some cvt nodes (starting with "m.) through "location.location.religions", which are some intermediate nodes. And they are in the end of Grounded Knowledge. Some Candidate Relations around the cvt nodes are given, among these, the relation "location.religion_percentage.religion" is relevant to obtain major religions, I can add it to current path, so that the path may meet my expectation. And I refine the relation 'location.location.religions' to the grounded relation "location.statistical_region.religions".
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion
#
Question: Rift Valley Province is located in a nation that uses which form of currency?

Initial Path: Rift Valley Province -> place.administrative_division.country -> place.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used

Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.location.geolocation -> m.046vy0w

Candidate Relations:['location.geocode.latitude', 'location.geocode.longitude', 'type.object.type']

Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, the path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
In Grounded Knowledge, the relation "place.administrative_division.country" is grounded to "location.administrative_division.country", the relation "place.location.geolocation" is grounded to "location.location.geolocation", and other relations from the Initial Path have not been grounded and some Candidate Relations are given.
Firstly, Rift Valley Province is connected to Kenya, through "location.administrative_division.country", which means Rift Valley Province is located in the nation Kenya, this meets part of my expectation. So I can refine the "place.administrative_division.country" to "location.administrative_division.country".
Secondly, Kenya is connected to a cvt node (starting with "m."), through "location.location.geolocation", which is an intermediate node. And it is in the end of Grounded Knowledge. Some Candidate Relations around this cvt node are given, and they seems about some geological information, with nothing about the currency. However, I need to know the currency used in Kenya to meet my expectation. I cannot find some relevant relation and the grounded relation "location.location.geolocation" seems irrelevant to the question. So I should replace "place.location.geolocation" with some relation to get the currency of Kenya.
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: Rift Valley Province -> location.administrative_division.country -> location.country.currency_used
#
"""


refine_prompt_path_one_path_add_stop_condition_1226 = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is a string, which is a path from the topic entity, connecting some relations to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. If the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This is given because some relations in the Initial Plan cannot be grounded, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. If Grounded Knowledge is sufficient to answer the question, or if it meets your expectations of the path, output ***STOP REFINE*** in the last line! If not, output Refine Path according to RULE 2.
2. Important! Your Refined Path must be in a string format starting from the topic entity, just the same format as the input Initial Path. Note that the path here is some relations connected by "->", and just the start point of the path is the topic entity. There is no other entities in this path!
3. You MUST NOT change the topic entity, which means the starting point of the Initial Plan and the Refined Plan must be exactly the same!
4. If the Candidate Relations is [] or empty, this means the Initial Path is fully grounded. If the Gounded Knowledge meets your expectation (contain necessary information to find the answer), you can just output ***STOP REFINE***. But if the Grounded Knowledge does not meet your expectation, this means the Initial Path has some parts irrelevant to the question. So refine the path on your own!
5. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, which means the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan.
6. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes (blank nodes) on Freebase knowledge base. These nodes can not be the answer, so if they are the end of path you must step forward according to Candidate Relations, or refine the previous path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity), based on the Question. After this, you should check if the Grounded Knowledge meets your expectations. If not, locate the irrelevant part, and refine the path.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, already meeting your expectation (reach the answer), just refine the relations in the Initial Path to the grounded ones. If there are still some relations ungrounded in Initial Plan, and Candididate Relations are given, this means the Initial Plan maybe is too long, just cut it.
3. Faithfulness: If some knowledge in Grounded Knowledge is irrelevant to this path, this means something in the Initial Path is unfaithful. Refine the plan. If some knowledge meets parts of your expectation, and some relations are not grounded, choose a relation in Candidate Relations (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty, or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should choose a relevant relation from the Candidate Relations of the topic entity,(or based on your own) to reconstruct the whole plan in order to get the answer.

Let me show you some examples.
# Question: The movie featured Miley Cyrus and was produced by Tobin Armbrust?

Initial Path: Miley Cyrus -> film.film.actor -> film.film.performance -> performance.performance.movies

Grounded Knowledge: Miley Cyrus -> film.actor.film -> m.010tw6z6 -> film.performance.film -> Wizards on Deck with Hannah Montana
Miley Cyrus -> film.actor.film -> m.0h0_35j -> film.performance.film -> The World According to Miley Cyrus
Miley Cyrus -> film.actor.film -> m.04g4mbv -> film.performance.film -> Bolt
Miley Cyrus -> film.actor.film -> m.0gvn_qx -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.0w2y18w -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.07ykl5g -> film.performance.film -> The Last Song
Miley Cyrus -> film.actor.film -> m.0vpd23v -> film.performance.film -> Hannah Montana and Miley Cyrus: Best of Both Worlds Concert
Miley Cyrus -> film.actor.film -> m.08c_hc1 -> film.performance.film -> Super Rhino
Miley Cyrus -> film.actor.film -> m.04g4mcc -> film.performance.film -> Big Fish
Miley Cyrus -> film.actor.film -> m.08cvslc -> film.performance.film -> Sonic the Hedgehog
Miley Cyrus -> film.actor.film -> m.0dls5z5 -> film.performance.film -> LOL

Candidate Relations: ['dataworld.gardening_hint.last_referenced_by', 'dataworld.gardening_hint.replaced_by', 'film.director.film', 'film.film.country', 'film.film.directed_by', 'film.film.genre', 'film.film.initial_release_date', 'film.film.language', 'film.film.prequel', 'film.film.release_date_s', 'film.film.runtime', 'film.film.sequel', 'film.film.starring', 'film.film.written_by', 'film.film_cut.film', 'film.film_genre.films_in_this_genre', 'film.film_regional_release_date.film', 'film.performance.film', 'film.writer.film', 'imdb.topic.title_id', 'kg.object_profile.prominent_type', 'tv.tv_director.episodes_directed', 'tv.tv_program.episodes', 'tv.tv_series_episode.air_date', 'tv.tv_series_episode.director', 'tv.tv_series_episode.episode_number', 'tv.tv_series_episode.next_episode', 'tv.tv_series_episode.season', 'tv.tv_series_episode.season_number', 'tv.tv_series_episode.series', 'tv.tv_series_episode.writer']

Thought: According to the initial path, this path starts from "Miley Cyrus". Based on the Question, this path should cover the film acted by Miley Cyrus, to reach the answer (expectation).
In the Grounded Knowledge, the relation "film.film.actor" is grounded to "film.actor.film" which seems relevant to film acting, and the relation "film.film.performance" is grounded to "film.performance.film" which seems relevant to film acting, and the relation "performance.performance.movies" is not grounded, and some Candidate Relations are given.
Firstly, I find that Miley Cyrus is connected to some cvt nodes (starting with "m."), through "film.actor.film", which are some intermediate nodes. They seem some films and I donnot know if they meet my expectation.
Secondly, I find that the cvt nodes are connected to some films, through "film.performance.film", so I obtain some films performed by Miley Cyrus. This already meets my expecation of this path.
So I just cut the relation after "performance.performance.movies", and we donnot need to further refine the path to get more information.

***STOP REFINE***
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?

Initial Path: United Kingdom -> location.location.religions -> place.religion.major_religions

Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_
United Kingdom -> location.location.contains -> Heaton railway station
United Kingdom -> location.location.contains -> Bakersfield, Nottingham
United Kingdom -> location.location.contains -> Knockloughrim
United Kingdom -> location.location.contains -> Oakenshaw

Candidate Relations: ['location.location.containedby', 'location.location.geolocation', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion', 'type.object.type']

Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom", to reach the answer (expectation).
In Grounded Knowledge, the relation "location.location.religions" is grounded to "location.statistical_region.religions" which seems relevant to the major religion and "location.location.contains" which seems irrelevant. And the relation "place.religion.major_religions" is not grounded, and some Candidate Relations connected to the end the Grounded Knowledge are given.
Firstly, I find that United Kingdom is connected to some cvt nodes (starting with "m.) through "location.location.religions", which are some intermediate nodes. And they are in the end of Grounded Knowledge. Some Candidate Relations around the cvt nodes are given, among these, the relation "location.religion_percentage.religion" is relevant to obtain major religions. 
So I replace the relation "location.location.religions" with "location.statistical_region.religions" to get the religion, and replace "place.religion.major_religions" to "location.religion_percentage.religion" to get the major religion .
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion
#
Question: Rift Valley Province is located in a nation that uses which form of currency?

Initial Path: Rift Valley Province -> place.administrative_division.country -> place.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used

Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.location.geolocation -> m.046vy0w

Candidate Relations: ['location.geocode.latitude', 'location.geocode.longitude']

Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, this path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
In Grounded Knowledge, the relation "place.administrative_division.country" is grounded to "location.administrative_division.country" which seems relevant to get the nation, the relation "place.location.geolocation" is grounded to "location.location.geolocation" which seems irrelevant to get the nation or the currency, and relations after this have not been grounded and some Candidate Relations are given.
Firstly, I find that Rift Valley Province is connected to Kenya, through "location.administrative_division.country", which means Rift Valley Province is located in the nation Kenya, this is relevant to the nation of "Rift Valley Province". So I replace "place.administrative_division.country" with "location.administrative_division.country".
Secondly, I find that Kenya is connected to a cvt node (starting with "m."), through "location.location.geolocation", which is an intermediate node. And it is in the end of Grounded Knowledge. Some Candidate Relations around this cvt node are given, and they seems some geological information, which seems irrelevant to get the nation or the currency of the nation. And I cannot find some relevant relation in Candidate Relations. So I should replace "place.location.geolocation" with some relation to get the currency of Kenya.
So I replace the relation "place.administrative_division.country" with "location.administrative_division.country" to get the nation, and replace the rest of the path to "location.country.currency_used" to get the currency of the country.
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: Rift Valley Province -> location.administrative_division.country -> location.country.currency_used
#
"""


refine_prompt_path_one_path_add_stop_condition_1227 = """Please refine a relation path from a topic entity to reach the answer of a question, according to some given information.

Here are some INFORMATION provided:
1. Question: Your ultimate goal is to find the relation paths are from a topic entity to the answer according to such question.
2. Initial Path: an initial relation path. The format is a string, which is a path from the topic entity, connecting some relations to reach the answer of the Question. Note that the path here is some relations connected by "->", and just the starting point of the path is the topic entity, there is no other entities are in this path!
3. Grounded Knowledge: some already-grounded knowledge paths, according to the Question and Initial Path. Each path, starting from a topic entity, is a grounded path of triple patterns in the knowledge graph. Note that the path here is some entities and relations connected by "->", where "A -> B -> C" means entity A can connect to entity C through relation B. The starting point of each path is a topic entity, the end point is either the answer(if the whole path is grounded) or an intermediate entity(some parts of the path is not grounded).
4. Candidate Relations: some possible candidate relations linking to the entities in end of Grounded Knowledge. If the Grounded knowledge is empty, Candidate Relations of topic entity will be shown. This is given because some relations in the Initial Plan cannot be grounded, so I provide you with some candidates to choose from, in order to refine the plan.

Here are some RULES you must obey:
1. If Grounded Knowledge is sufficient to answer the question, or if it meets your expectations of the path, output ***STOP REFINE*** in the last line! If not, output Refine Path according to RULE 2.
2. Important! Your Refined Path must be in a string format starting from the topic entity, just the same format as the input Initial Path. Note that the path here is some relations connected by "->", and just the start point of the path is the topic entity. There is no other entities in this path!
3. You MUST NOT change the topic entity, which means the starting point of the Initial Plan and the Refined Plan must be exactly the same!
4. If the Candidate Relations is [] or empty, this means the Initial Path is fully grounded. If the Gounded Knowledge meets your expectation (contain necessary information to find the answer), you can just output ***STOP REFINE***. But if the Grounded Knowledge does not meet your expectation, this means the Initial Path has some parts irrelevant to the question. So refine the path on your own!
5. You should just refine the given path from the topic entity to the answer. If a Question has multiple topic entities, which means the answer is constrained by multiple paths, or the answer is the intersection of multiple paths from different topic entities. No worries, just refine the one path (from topic entity to answer) in the Initial Plan.
6. If you encounter some entities in Grounded Knowledge starting with "m." or "g.", this means the entities are cvt nodes (blank nodes) on Freebase knowledge base. These nodes can not be the answer, so if they are the end of path you must step forward according to Candidate Relations, or refine the previous path.

Here are some practical tips for you to refine the plan (just some tips for you to consider, you donnot have to choose only from these):
1. Path expectation: Identify critical relations needed to included in this path (starting from a topic entity), based on the Question. After this, you should check if the Grounded Knowledge meets your expectations. If not, locate the irrelevant part, and refine the path.
2. Sufficiency: If the Grounded Knowledge is already sufficient in this path, already meeting your expectation (reach the answer), just refine the relations in the Initial Path to the grounded ones. If there are still some relations ungrounded in Initial Plan, and Candididate Relations are given, this means the Initial Plan maybe is too long, just cut it.
3. Faithfulness: If some knowledge in Grounded Knowledge is irrelevant to this path, this means something in the Initial Path is unfaithful. Refine the plan. If some knowledge meets parts of your expectation, and some relations are not grounded, choose a relation in Candidate Relations (or you can refine the whole plan, or just part of it, or add some relations, or change some relations, it depends on you).
4. Necessity: If the Grounded Knowledge is empty, or relations of a topic entity is shown in Candidate Relations, this means no relations is grounded, something necessarily to answer the question is not given in the Initial Plan. So you should choose a relevant relation from the Candidate Relations of the topic entity,(or based on your own) to reconstruct the whole plan in order to get the answer.

Let me show you some examples.
# Question: The movie featured Miley Cyrus and was produced by Tobin Armbrust?

Initial Path: Miley Cyrus -> film.film.actor -> film.film.performance

Grounded Knowledge: Miley Cyrus -> film.actor.film -> m.010tw6z6 -> film.performance.film -> Wizards on Deck with Hannah Montana
Miley Cyrus -> film.actor.film -> m.0h0_35j -> film.performance.film -> The World According to Miley Cyrus
Miley Cyrus -> film.actor.film -> m.04g4mbv -> film.performance.film -> Bolt
Miley Cyrus -> film.actor.film -> m.0gvn_qx -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.0w2y18w -> film.performance.film -> So Undercover
Miley Cyrus -> film.actor.film -> m.07ykl5g -> film.performance.film -> The Last Song
Miley Cyrus -> film.actor.film -> m.0vpd23v -> film.performance.film -> Hannah Montana and Miley Cyrus: Best of Both Worlds Concert
Miley Cyrus -> film.actor.film -> m.08c_hc1 -> film.performance.film -> Super Rhino
Miley Cyrus -> film.actor.film -> m.04g4mcc -> film.performance.film -> Big Fish
Miley Cyrus -> film.actor.film -> m.08cvslc -> film.performance.film -> Sonic the Hedgehog
Miley Cyrus -> film.actor.film -> m.0dls5z5 -> film.performance.film -> LOL

Candidate Relations: []

Thought: According to the initial path, this path starts from "Miley Cyrus". Based on the Question, this path should cover the film acted by Miley Cyrus, to reach the answer (expectation).
In the Grounded Knowledge, the relation "film.film.actor" is grounded to "film.actor.film" which seems relevant to film acting, and the relation "film.film.performance" is grounded to "film.performance.film" which seems relevant to film acting.
Firstly, I find that Miley Cyrus is connected to some cvt nodes (starting with "m."), through "film.actor.film", which are some intermediate nodes. They seem some films and I donnot know if they meet my expectation.
Secondly, I find that the cvt nodes are connected to some films, through "film.performance.film", so I obtain some films performed by Miley Cyrus. This already meets my expecation of this path.
So this whole path is grounded and meets my expectation. 
So I think we donnot need to further refine the path to get more information.

***STOP REFINE***
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?

Initial Path: United Kingdom -> location.location.religions -> place.religion.major_religions

Grounded Knowledge: United Kingdom -> location.statistical_region.religions -> m.047hrrd
United Kingdom -> location.statistical_region.religions -> m.043trcf
United Kingdom -> location.statistical_region.religions -> m.047hrrr
United Kingdom -> location.statistical_region.religions -> m.047hrqc
United Kingdom -> location.statistical_region.religions -> m.047hrr4
United Kingdom -> location.statistical_region.religions -> m.047hrr_
United Kingdom -> location.location.contains -> Heaton railway station
United Kingdom -> location.location.contains -> Bakersfield, Nottingham
United Kingdom -> location.location.contains -> Knockloughrim
United Kingdom -> location.location.contains -> Oakenshaw

Candidate Relations: ['location.location.containedby', 'location.location.geolocation', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion', 'type.object.type']

Thought: According to Initial Plan, this path starts from "United Kingdom". Based on the Question, this path should cover the major religion in "United Kingdom", to reach the answer (expectation).
In Grounded Knowledge, the relation "location.location.religions" is grounded to "location.statistical_region.religions" which seems relevant to the major religion and "location.location.contains" which seems irrelevant. And the relation "place.religion.major_religions" is not grounded, and some Candidate Relations connected to the end the Grounded Knowledge are given.
Firstly, I find that United Kingdom is connected to some cvt nodes (starting with "m.) through "location.location.religions", which are some intermediate nodes. And they are in the end of Grounded Knowledge. Some Candidate Relations around the cvt nodes are given, among these, the relation "location.religion_percentage.religion" is relevant to obtain major religions. 
So I replace the relation "location.location.religions" with "location.statistical_region.religions" to get the religion, and replace "place.religion.major_religions" to "location.religion_percentage.religion" to get the major religion .
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: United Kingdom -> location.statistical_region.religions -> location.religion_percentage.religion
#
Question: Rift Valley Province is located in a nation that uses which form of currency?

Initial Path: Rift Valley Province -> place.administrative_division.country -> place.location.geolocation -> location.mailing_address.state_province_region -> place.country.currency_used

Grounded Knowledge: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.location.geolocation -> m.046vy0w

Candidate Relations: ['location.geocode.latitude', 'location.geocode.longitude']

Thought: According to the initial path, this path starts from "Rift Valley Province". Based on the Question, this path should firstly cover the nation where "Rift Valley Province" located, and then, the form of currency used in this nation, to reach the answer (expectation).
In Grounded Knowledge, the relation "place.administrative_division.country" is grounded to "location.administrative_division.country" which seems relevant to get the nation, the relation "place.location.geolocation" is grounded to "location.location.geolocation" which seems irrelevant to get the nation or the currency, and relations after this have not been grounded and some Candidate Relations are given.
Firstly, I find that Rift Valley Province is connected to Kenya, through "location.administrative_division.country", which means Rift Valley Province is located in the nation Kenya, this is relevant to the nation of "Rift Valley Province". So I replace "place.administrative_division.country" with "location.administrative_division.country".
Secondly, I find that Kenya is connected to a cvt node (starting with "m."), through "location.location.geolocation", which is an intermediate node. And it is in the end of Grounded Knowledge. Some Candidate Relations around this cvt node are given, and they seems some geological information, which seems irrelevant to get the nation or the currency of the nation. And I cannot find some relevant relation in Candidate Relations. So I should replace "place.location.geolocation" with some relation to get the currency of Kenya.
So I replace the relation "place.administrative_division.country" with "location.administrative_division.country" to get the nation, and replace the rest of the path to "location.country.currency_used" to get the currency of the country.
Therefore, the answer has not been reached. The Refined Path is as follow.

Refined Path: Rift Valley Province -> location.administrative_division.country -> location.country.currency_used
#
"""



extract_relation_prompt = """Please retrieve %s relations (separated by semicolon) that contribute to the question and rate their contribution on a scale from 0 to 1 (the sum of the scores of %s relations is 1).
Q: Name the president of the country whose main spoken language was Brahui in 1980?
Topic Entity: Brahui Language
Relations: language.human_language.main_country; language.human_language.language_family; language.human_language.iso_639_3_code; base.rosetta.languoid.parent; language.human_language.writing_system; base.rosetta.languoid.languoid_class; language.human_language.countries_spoken_in; kg.object_profile.prominent_type; base.rosetta.languoid.document; base.ontologies.ontology_instance.equivalent_instances; base.rosetta.languoid.local_name; language.human_language.region
A: 1. {language.human_language.main_country (Score: 0.4))}: This relation is highly relevant as it directly relates to the country whose president is being asked for, and the main country where Brahui language is spoken in 1980.
2. {language.human_language.countries_spoken_in (Score: 0.3)}: This relation is also relevant as it provides information on the countries where Brahui language is spoken, which could help narrow down the search for the president.
3. {base.rosetta.languoid.parent (Score: 0.2)}: This relation is less relevant but still provides some context on the language family to which Brahui belongs, which could be useful in understanding the linguistic and cultural background of the country in question.

Q: """

score_entity_candidates_prompt = """Please score the entities' contribution to the question on a scale from 0 to 1 (the sum of the scores of all entities is 1).
Q: The movie featured Miley Cyrus and was produced by Tobin Armbrust?
Relation: film.producer.film
Entites: The Resident; So Undercover; Let Me In; Begin Again; The Quiet Ones; A Walk Among the Tombstones
Score: 0.0, 1.0, 0.0, 0.0, 0.0, 0.0
The movie that matches the given criteria is "So Undercover" with Miley Cyrus and produced by Tobin Armbrust. Therefore, the score for "So Undercover" would be 1, and the scores for all other entities would be 0.

Q: {}
Relation: {}
Entites: """

answer_prompt = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets and your knowledge.
Q: Find the person who said \"Taste cannot be controlled by law\", what did this person die from?
Knowledge Triplets: Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson
A: Based on the given knowledge triplets, it's not sufficient to answer the entire question. The triplets only provide information about the person who said "Taste cannot be controlled by law," which is Thomas Jefferson. To answer the second part of the question, it's necessary to have additional knowledge about where Thomas Jefferson's dead.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter, book.written_work.author, Laura Ingalls Wilder
Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity
Unknown-Entity, people.place_lived.location, De Smet
A: Based on the given knowledge triplets, the author of The Long Winter, Laura Ingalls Wilder, lived in De Smet. Therefore, the answer to the question is {De Smet}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens
Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens
Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group
A: Based on the given knowledge triplets, the coach of the team owned by Steve Bisciotti is not explicitly mentioned. However, it can be inferred that the team owned by Steve Bisciotti is the Baltimore Ravens, a professional sports team. Therefore, additional knowledge about the current coach of the Baltimore Ravens can be used to answer the question.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province, location.administrative_division.country, Kenya
Rift Valley Province, location.location.geolocation, UnName_Entity
Rift Valley Province, location.mailing_address.state_province_region, UnName_Entity
Kenya, location.country.currency_used, Kenyan shilling
A: Based on the given knowledge triplets, Rift Valley Province is located in Kenya, which uses the Kenyan shilling as its currency. Therefore, the answer to the question is {Kenyan shilling}.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, UnName_Entity
National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti
National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés
UnName_Entity, government.national_anthem_of_a_country.country, Bolivia
Bolivia, location.country.national_anthem, UnName_Entity
A: Based on the given knowledge triplets, we can infer that the National Anthem of Bolivia is the anthem of Bolivia. Therefore, the country with the National Anthem of Bolivia is Bolivia itself. However, the given knowledge triplets do not provide information about which nations border Bolivia. To answer this question, we need additional knowledge about the geography of Bolivia and its neighboring countries.

Q: {}
"""


# system prompt 假设不包含 就用CoT
answer_prompt_kb = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets and your knowledge.
Q: Find the person who said \"Taste cannot be controlled by law\", what did this person die from?
Knowledge Triplets: (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson)
A: Based on the given knowledge triplets, it's not sufficient to answer the entire question. The triplets only provide information about the person who said "Taste cannot be controlled by law," which is Thomas Jefferson. To answer the second part of the question, it's necessary to have additional knowledge about where Thomas Jefferson's dead.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: (The Long Winter, book.written_work.author, Laura Ingalls Wilder)
(Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity)
(Unknown-Entity, people.place_lived.location, De Smet)
A: Based on the given knowledge triplets, the author of The Long Winter, Laura Ingalls Wilder, lived in De Smet. Therefore, the answer to the question is {De Smet}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens)
(Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens)
(Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group)
A: Based on the given knowledge triplets, the coach of the team owned by Steve Bisciotti is not explicitly mentioned. However, it can be inferred that the team owned by Steve Bisciotti is the Baltimore Ravens, a professional sports team. Therefore, additional knowledge about the current coach of the Baltimore Ravens can be used to answer the question.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, Kenya)
(Rift Valley Province, location.location.geolocation, UnName_Entity)
(Rift Valley Province, location.mailing_address.state_province_region, UnName_Entity)
(Kenya, location.country.currency_used, Kenyan shilling)
A: Based on the given knowledge triplets, Rift Valley Province is located in Kenya, which uses the Kenyan shilling as its currency. Therefore, the answer to the question is {Kenyan shilling}.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, UnName_Entity)
(National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti)
(National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés)
(UnName_Entity, government.national_anthem_of_a_country.country, Bolivia)
(Bolivia, location.country.national_anthem, UnName_Entity)
A: Based on the given knowledge triplets, we can infer that the National Anthem of Bolivia is the anthem of Bolivia. Therefore, the country with the National Anthem of Bolivia is Bolivia itself. However, the given knowledge triplets do not provide information about which nations border Bolivia. To answer this question, we need additional knowledge about the geography of Bolivia and its neighboring countries.

"""


# If the knowledge triples is conflict with your knowledge, use the provided knowledge as reference. 

answer_prompt_kb_interwined_path = """Given a question and the associated retrieved knowledge graph path (entities and relations connected by "->"), please answer the question with these paths. If the given knowledge paths are not insuffienct, you can use your own knowledge. Use \{\} to enclose the answer! Please think step by step!
Q: Find the person who said \"Taste cannot be controlled by law\", where did this person die?
Knowledge Paths: \"Taste cannot be controlled by law.\" -> media_common.quotation.author -> Thomas Jefferson
A: For this question, I should first know the person who quotes \"Taste cannot be controlled by law.\", and then where did the person die. 
First, based on "\"Taste cannot be controlled by law.\" -> media_common.quotation.author -> Thomas Jefferson", The person who said \"Taste cannot be controlled by law\" is Thomas Jefferson. 
Second, no path provided can answer where did Thomas Jefferson die, however, based on my own knowledge, Thomas Jefferson died in Charlottesville. 
So, the answer is { Charlottesville }.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter -> book.written_work.author -> Laura Ingalls Wilder -> people.person.places_lived -> m.28e5697 -> people.place_lived.location -> De Smet
A: For this question, I should first know the person who is the artist nominated for The Long Winter, and then where did the person live.
First, based on "The Long Winter -> book.written_work.author -> Laura Ingalls Wilder", the author of The Long Winter is Laura Ingalls Wilder. 
Second, based on "Laura Ingalls Wilder -> people.person.places_lived -> m.28e5697 -> people.place_lived.location -> De Smet", Laura Ingalls Wilder lived in De Smet. 
So, the answer is { De Smet }.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Paths: Steve Bisciotti -> sports.professional_sports_team.owner_s -> Baltimore Ravens
Steve Bisciotti -> sports.sports_team_owner.teams_owned -> Baltimore Ravens
Steve Bisciotti -> organization.organization_founder.organizations_founded -> Allegis Group
A: For this question, I should first know the team owned by Steve Bisciotti, and then the coach of the team.
First, based on "Steve Bisciotti -> sports.professional_sports_team.owner_s -> Baltimore Ravens" and "Steve Bisciotti -> sports.sports_team_owner.teams_owned -> Baltimore Ravens", the team owned by Steve Bisciotti is the Baltimore Ravens. 
Second, no Triplet provided can answer who is the coach of the Baltimore Ravens, however, based on my owned knowledge, the coach of the Baltimore Ravens, is John Harbaugh.
So, the answer is { John Harbaugh }.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province -> location.administrative_division.country -> Kenya -> location.country.currency_used -> Kenyan shilling
Rift Valley Province -> location.location.geolocation -> m.02_pgyk -> location.mailing_address.state_province_region -> Rift Valley Province 
Rift Valley Province -> location.mailing_address.state_province_region -> Rift Valley Province
A: For this question, I should first know Rift Valley Province is located in which nation, and then the form of currency used in that nation.
First, based on "Rift Valley Province -> location.administrative_division.country -> Kenya", Rift Valley Province is located in Kenya. 
Second, based on "Kenya -> location.country.currency_used -> Kenyan shilling", form of currency used in Kenyan is Kenyan shilling. 
So the answer is { Kenyan shilling }.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: National Anthem of Bolivia -> government.national_anthem_of_a_country.anthem -> m.54679ee -> government.national_anthem_of_a_country.country -> Bolivia -> location.country.national_anthem, National Anthem of Bolivia
National Anthem of Bolivia -> music.composition.composer -> Leopoldo Benedetto Vincenti
National Anthem of Bolivia -> music.composition.lyricist -> José Ignacio de Sanjinés
A: For this question, I should first know which country has the national anthem, the National Anthem of Bolivia, and then nations bordering this nation.
First, based on (Bolivia, location.country.national_anthem, National Anthem of Bolivia), (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, intermediate_entity_1), (intermediate_entity_1, government.national_anthem_of_a_country.country, Bolivia), the country with the National Anthem of Boliviathe National Anthem of Bolivia is Bolivia. Second, no Triplet provided can answer Bolivia borders which country, however, based on my owned knowledge, the countries border Bolivia are Brazil, Peru, Chile, Paraguay and Argentina. So, the answer is {Brazil, Peru, Chile, Paraguay and Argentina}.

"""




# 具体到用了哪条知识，用不到就用CoT
answer_prompt_kb_interwined = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets. If the given knowledge triples is not enough or missing, you can use your own knowledge. Use \{\} to enclose the answer! Please think step by step.
Q: Find the person who said \"Taste cannot be controlled by law\", where did this person die ?
Knowledge Triplets: (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson)
A: First, based on (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson), the person who said \"Taste cannot be controlled by law\" is Thomas Jefferson. Second, no Triplet provided can answer where Thomas Jefferson's dead, however, based on my owned knowledge, Thomas Jefferson died in Charlottesville. So, the answer is { Charlottesville }.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: (The Long Winter, book.written_work.author, Laura Ingalls Wilder)
(Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity)
(Unknown-Entity, people.place_lived.location, De Smet)
A: First, based on (The Long Winter, book.written_work.author, Laura Ingalls Wilder), the author of The Long Winter is Laura Ingalls Wilder. Second, based on (Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity), (Unknown-Entity, people.place_lived.location, De Smet), Laura Ingalls Wilder lived in De Smet. So, the answer is {De Smet}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens)
(Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens)
(Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group)
A: First, based on (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens), (Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens), the team owned by Steve Bisciotti is the Baltimore Ravens. Second, no Triplet provided can answer who is the coach of the Baltimore Ravens, however, based on my owned knowledge, the coach of the Baltimore Ravens, is John Harbaugh. So, the answer is {John Harbaugh}.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, Kenya)
(Rift Valley Province, location.location.geolocation, intermediate_entity_1)
(Rift Valley Province, location.mailing_address.state_province_region, intermediate_entity_2)
(Kenya, location.country.currency_used, Kenyan shilling)
A: First, based on (Rift Valley Province, location.administrative_division.country, Kenya), Rift Valley Province is located in Kenya. Second, based on (Kenya, location.country.currency_used, Kenyan shilling), form of currency used in Kenyan is Kenyan shilling. So the answer is {Kenyan shilling}.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, intermediate_entity_1)
(National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti)
(National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés)
(intermediate_entity_1, government.national_anthem_of_a_country.country, Bolivia)
(Bolivia, location.country.national_anthem, National Anthem of Bolivia)
A: First, based on (Bolivia, location.country.national_anthem, National Anthem of Bolivia), (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, intermediate_entity_1), (intermediate_entity_1, government.national_anthem_of_a_country.country, Bolivia), the country with the National Anthem of Boliviathe National Anthem of Bolivia is Bolivia. Second, no Triplet provided can answer Bolivia borders which country, however, based on my owned knowledge, the countries border Bolivia are Brazil, Peru, Chile, Paraguay and Argentina. So, the answer is {Brazil, Peru, Chile, Paraguay and Argentina}.

"""


# 空白节点直接用本身的id
answer_prompt_kb_interwined_nointer = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets. If the given knowledge triples is not enough or missing, you can use your own knowledge. Use \{\} to enclose the answer! Please think step by step.
Q: Find the person who said \"Taste cannot be controlled by law\", where did this person die?
Knowledge Triplets: (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson)
A: First, based on (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson), the person who said \"Taste cannot be controlled by law\" is Thomas Jefferson. Second, no Triplet provided can answer where Thomas Jefferson's dead, however, based on my owned knowledge, Thomas Jefferson died in Charlottesville. So, the answer is { Charlottesville }.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: (The Long Winter, book.written_work.author, Laura Ingalls Wilder)
(Laura Ingalls Wilder, people.person.places_lived, m.28e5697)
(m.28e5697, people.place_lived.location, De Smet)
A: First, based on (The Long Winter, book.written_work.author, Laura Ingalls Wilder), the author of The Long Winter is Laura Ingalls Wilder. Second, based on (Laura Ingalls Wilder, people.person.places_lived, m.28e5697), (m.28e5697, people.place_lived.location, De Smet), Laura Ingalls Wilder lived in De Smet. So, the answer is {De Smet}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens)
(Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens)
(Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group)
A: First, based on (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens), (Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens), the team owned by Steve Bisciotti is the Baltimore Ravens. Second, no Triplet provided can answer who is the coach of the Baltimore Ravens, however, based on my owned knowledge, the coach of the Baltimore Ravens, is John Harbaugh. So, the answer is {John Harbaugh}.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, Kenya)
(Rift Valley Province, location.location.geolocation, m.159ss4)
(Rift Valley Province, location.mailing_address.state_province_region, m.465s98_)
(Kenya, location.country.currency_used, Kenyan shilling)
A: First, based on (Rift Valley Province, location.administrative_division.country, Kenya), Rift Valley Province is located in Kenya. Second, based on (Kenya, location.country.currency_used, Kenyan shilling), form of currency used in Kenyan is Kenyan shilling. So the answer is {Kenyan shilling}.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, m.54679ee)
(National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti)
(National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés)
(m.54679ee, government.national_anthem_of_a_country.country, Bolivia)
(Bolivia, location.country.national_anthem, National Anthem of Bolivia)
A: First, based on (Bolivia, location.country.national_anthem, National Anthem of Bolivia), (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, m.54679ee), (m.54679ee, government.national_anthem_of_a_country.country, Bolivia), the country with the National Anthem of Boliviathe National Anthem of Bolivia is Bolivia. Second, no Triplet provided can answer Bolivia borders which country, however, based on my owned knowledge, the countries border Bolivia are Brazil, Peru, Chile, Paraguay and Argentina. So, the answer is {Brazil, Peru, Chile, Paraguay and Argentina}.

"""



answer_prompt_kb_interwined_q_after = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets. If the given knowledge triples is not enough or missing, you can use your own knowledge. Please think step by step.
Knowledge Triplets: (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson)
Q: Find the person who said \"Taste cannot be controlled by law\", where did this person die ?
A: First, based on (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson), the person who said \"Taste cannot be controlled by law\" is Thomas Jefferson. Second, no Triplet provided can answer where Thomas Jefferson's dead, however, based on my owned knowledge, Thomas Jefferson died in Charlottesville. So, the answer is { Charlottesville }.

Knowledge Triplets: (The Long Winter, book.written_work.author, Laura Ingalls Wilder)
(Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity)
(Unknown-Entity, people.place_lived.location, De Smet)
Q: The artist nominated for The Long Winter lived where?
A: First, based on (The Long Winter, book.written_work.author, Laura Ingalls Wilder), the author of The Long Winter is Laura Ingalls Wilder. Second, based on (Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity), (Unknown-Entity, people.place_lived.location, De Smet), Laura Ingalls Wilder lived in De Smet. So, the answer is {De Smet}.

Knowledge Triplets: (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens)
(Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens)
(Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group)
Q: Who is the coach of the team owned by Steve Bisciotti?
A: First, based on (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens), (Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens), the team owned by Steve Bisciotti is the Baltimore Ravens. Second, no Triplet provided can answer who is the coach of the Baltimore Ravens, however, based on my owned knowledge, the coach of the Baltimore Ravens, is John Harbaugh. So, the answer is {John Harbaugh}.

Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, Kenya)
(Rift Valley Province, location.location.geolocation, intermediate_entity_1)
(Rift Valley Province, location.mailing_address.state_province_region, intermediate_entity_2)
(Kenya, location.country.currency_used, Kenyan shilling)
Q: Rift Valley Province is located in a nation that uses which form of currency?
A: First, based on (Rift Valley Province, location.administrative_division.country, Kenya), Rift Valley Province is located in Kenya. Second, based on (Kenya, location.country.currency_used, Kenyan shilling), form of currency used in Kenyan is Kenyan shilling. So the answer is {Kenyan shilling}.

Knowledge Triplets: (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, intermediate_entity_1)
(National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti)
(National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés)
(intermediate_entity_1, government.national_anthem_of_a_country.country, Bolivia)
(Bolivia, location.country.national_anthem, National Anthem of Bolivia)
Q: The country with the National Anthem of Bolivia borders which nations?
A: First, based on (Bolivia, location.country.national_anthem, National Anthem of Bolivia), (National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, intermediate_entity_1), (intermediate_entity_1, government.national_anthem_of_a_country.country, Bolivia), the country with the National Anthem of Boliviathe National Anthem of Bolivia is Bolivia. Second, no Triplet provided can answer Bolivia borders which country, however, based on my owned knowledge, the countries border Bolivia are Brazil, Peru, Chile, Paraguay and Argentina. So, the answer is {Brazil, Peru, Chile, Paraguay and Argentina}.

"""


kb_extract_prompt = """Given a freebase sparql query and the corresponding answer of the query,  you are asked to extract knowledge graph triplets (entity, relation, entity) from the query and answer.
Sparql: PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?x\nWHERE{\nTaste cannot be controlled by law. ns:media_common.quotation.author ?x\n}
Answer: Thomas Jefferson
Knowledge Triplets: (Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson)

Sparql: SELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\nThe Long Winter ns:book.written_work.author Laura Ingalls Wilder .\nLaura Ingalls Wilder ns:people.person.places_lived ?c .\n?c ns:people.place_lived.location ?x . \n}
Answer: De Smet
Knowledge Triplets: (The Long Winter, book.written_work.author, Laura Ingalls Wilder)
(Laura Ingalls Wilder, people.person.places_lived, intermediate_entity_c)
(intermediate_entity_c, people.place_lived.location, De Smet)

Sparql: SELECT DISTINCT ?x\nWHERE {\nSteve Bisciotti ns:sports.professional_sports_team.owner_s Baltimore Ravens .\nBaltimore Ravens ns:sports.sports_team_coach.teams_coach ?x \n}
Answer: JC Smith
Knowledge Triplets: (Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens)
(Baltimore Ravens, sports.sports_team_coach.teams_coach, JC Smith)

Sparql: SELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\nRift Valley Province ns:location.administrative_division.country ?c.\n ?c ns:location.country.currency_used ?x\n}
Answer: Kenyan shilling
Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, intermediate_entity_c)
(intermediate_entity_c, location.country.currency_used, Kenyan shilling)

Sparql: SELECT DISTINCT ?x\nWHERE {\nFILTER (?x != ?c)\nRift Valley Province ns:location.administrative_division.country ?c.\n ?c ns:location.country.currency_used ?x\n}
Answer: Kenyan shilling
Knowledge Triplets: (Rift Valley Province, location.administrative_division.country, intermediate_entity_c)
(intermediate_entity_c, location.country.currency_used, Kenyan shilling)

Sparql: SELECT DISTINCT ?x\nWHERE {\nthe Cleveland Browns ns:sports.professional_sports_team.draft_picks ?y .\n?y ns:sports.sports_league_draft_pick.player ?x .\n?x ns:sports.pro_athlete.career_start ?num .\nFILTER (?num < "2007"^^xsd:dateTime)\n}
Answer: Kamerion Wimbley, Jeff Faine, Braylon Edwards, Kellen Winslow II
Knowledge Triplets: (the Cleveland Browns, sports.professional_sports_team.draft_picks, intermediate_entity_y)
(intermediate_entity_y, sports.sports_league_draft_pick.player, Kamerion Wimbley / Jeff Faine / Braylon Edwards / Kellen Winslow II)
(Kamerion Wimbley / Jeff Faine / Braylon Edwards / Kellen Winslow II, sports.pro_athlete.career_start, intermediate_entity_num)
(intermediate_entity_num, <, 2007)

"""


kb_contract_prompt_dev_short = """Given a question and a set of knowledge triples, trim the triples according to the question, the remaining triples are only necessary to answer the question.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge Triples: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Trimed Triples: (New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.languages_spoken, Західнофламандська група діалектів )\n(Bélgica, location.country.capital, Brussel )
Trimed Triples: (Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)

Q: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )
Trimed Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

"""


kb_contract_prompt_dev_internal = """Given a question and a set of knowledge triples, output relevant knowledge triples. You should trimed the knowledge irrelevant of the question. The remaining knowledge is necessary to answer the question. Note that some knowledge is not enough to answer the question, if so, you can infer some knowledge based on given knowledge triples and your own knowledge. DONNOT change the knowledge, but you can infer or add your own knowledge.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge Triples: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Relevant Triples: (New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.languages_spoken, Bélgican )\n(Bélgica, location.country.capital, City of Brussels)
Relevant Triples: (Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)

Question: Where is the college with the team South Carolina Gamecocks men's basketball team located in?
Knowledge Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )\n(University of South Carolina, location.location.containedby, South Carolina)
Relevant Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(University of South Carolina, location.location.containedby, South Carolina )

Question: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.place_of_birth.place, California)
Relevant Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

Question: People from the location that appointed Adly Mansour to governmental position speak what languages?
Knowledge Triples: (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\n(Adly Mansour, people.person.nationality, Egypt)\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)
Relevant Triples: (Adly Mansour, people.person.nationality, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)

Question: Obama is the president of which country?
Knowledge Triples: (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America)\n(Obama, people.place_of_birth.country, America)
Relevant Triples: (Obama, people.occupation.president_of, America)

"""


kb_contract_prompt_dev_internal_nointer = """Given a question and a set of knowledge triples, output relevant knowledge triples. You should trimed the knowledge irrelevant of the question. The remaining knowledge is necessary to answer the question. Note that some knowledge is not enough to answer the question, if so, you can infer some knowledge based on given knowledge triples and your own knowledge. DONNOT change the knowledge, but you can infer or add your own knowledge.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge Triples: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Relevant Triples: (New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.languages_spoken, Bélgican )\n(Bélgica, location.country.capital, City of Brussels)
Relevant Triples: (Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)

Question: Where is the college with the team South Carolina Gamecocks men's basketball team located in?
Knowledge Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )\n(University of South Carolina, location.location.containedby, South Carolina)
Relevant Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(University of South Carolina, location.location.containedby, South Carolina )

Question: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.place_of_birth.place, California)
Relevant Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

Question: People from the location that appointed Adly Mansour to governmental position speak what languages?
Knowledge Triples: (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\n(Adly Mansour, people.person.nationality, Egypt)\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)
Relevant Triples: (Adly Mansour, people.person.nationality, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)

Question: Obama is the president of which country?
Knowledge Triples: (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America)\n(Obama, people.place_of_birth.country, America)
Relevant Triples: (Obama, people.occupation.president_of, America)

"""



kb_contract_prompt_dev_internal_reasoning = """Given a question and a set of knowledge triples, output Refined knowledge. You should trimed the knowledge irrelevant of the question. The remaining knowledge is necessary to answer the question. Note that some knowledge is not enough to answer the question, if so, you can infer some knowledge based on given knowledge triples and your own knowledge. DONNOT change the knowledge, but you can infer or add your own knowledge.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge Triples: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Reasoning: First, we should knowledge the champion of the 1999 World Series, which can be answered by (New York Yankees, sports.sports_team.championships, 1999 World Series). Second, we should know when New York Yankees win their first World Series, according to the knowledge triples, the knowledge should be (New York Yankees, sports.sports_team.championships, 1923 World Series). 
According to reasoning, triples to answer Question:(New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.official_language, French )\n(Bélgica, location.country.official_language, German Language )\n(Bélgica, location.country.languages_spoken, Bélgican )\n(Bélgica, location.country.capital, City of Brussels)
Reasoning: First, we should know the country with the capital Brussel, which can be answered by (Bélgica, location.country.capital, City of Brussels). Second, we should know people from Bélgica speak what languages, according to the knowledge triples, the knowledge should be (Bélgica, location.country.official_language, Dutch Language)(Bélgica, location.country.official_language, French )(Bélgica, location.country.official_language, German Language )
According to reasoning, triples to answer Question:(Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)\n(Bélgica, location.country.official_language, French )\n(Bélgica, location.country.official_language, German Language )

Question: Where is the college with the team South Carolina Gamecocks men's basketball team located in?
Knowledge Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )
Reasoning: First, we should knowledgethe college with the team South Carolina Gamecocks men's basketball team, which can be answered by (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball). Second, we should know where is the University of South Carolina, which is not covered by the given knowledge, however, based on my own knowledge, and the given knowledge (South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina ), it can be inferred that (University of South Carolina, location.location.containedby, South Carolina) is necessary to answer the question.
According to reasoning, triples to answer Question:(University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(University of South Carolina, location.location.containedby, South Carolina )

Question: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.cause_of_death.people, Lung Cancer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.place_of_birth.place, California)
Reasoning: First, we should know the artist that went on Live & more Encore Tour, which can be answered by (Live & More Encore Tour, music.concert_tour.artist, Donna Summer ). Second, we should know the cause of death to the Donna Summer, which can be answered by (Lung cancer, people.cause_of_death.people, Donna Summer ).
According to reasoning, triples to answer Question:(Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

Question: People from the location that appointed Adly Mansour to governmental position speak what languages?
Knowledge Triples: (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\n(Adly Mansour, people.person.nationality, Egypt)\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)
Reasoning: First, we should know the location that appointed Adly Mansour to governmental position, which is not covered by the given knowledge, however, based on my knowledge and the given knowledge (Adly Mansour, people.person.nationality, Egypt), it can be inferred that (Egypt, government.governmental.governmental_position, Adly Mansour) is necessary to answer the question. Second, we should know people from Egypt speak what language, which can be answered by (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt).
According to reasoning, triples to answer Question:(Egypt, government.governmental.governmental_position, Adly Mansour)\n(Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)

Question: Obama is the president of which country?
Knowledge Triples: (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America)\n(Obama, people.place_of_birth.country, America)
Reasoning: First, we should know Obama is the president of which country, which is not covered by the given knowledge, however, based on my knowledge and the given knowledge (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America) (Obama, people.place_of_birth.country, America), it can be inferred that the knowledge (Obama, people.people_occupation.president_of, America) is necessary to answer the question.
According to reasoning, triples to answer Question:(Obama, people.people_occupation.president_of, America)

"""

kb_contract_prompt_dev_internal_reasoning_1129 = """Given a question and a set of knowledge triples, output relevant knowledge triples. You should trimed the knowledge irrelevant of the question. The remaining knowledge is necessary to answer the question. Note that some knowledge is not enough to answer the question, if so, you can infer some knowledge based on given knowledge triples and your own knowledge. DONNOT change the knowledge, but you can infer or add your own knowledge.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Reasoning: First, we should know the champion of the 1999 World Series, which can be answered by (New York Yankees, sports.sports_team.championships, 1999 World Series). Second, we should know when New York Yankees win their first World Series, according to the knowledge triples, the knowledge should be (New York Yankees, sports.sports_team.championships, 1923 World Series). 
Refined Knowledge: (New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.official_language, French )\n(Bélgica, location.country.official_language, German Language )\n(Bélgica, location.country.languages_spoken, Bélgican )\n(Bélgica, location.country.capital, City of Brussels)
Reasoning: First, we should know the country with the capital Brussel, which can be answered by (Bélgica, location.country.capital, City of Brussels). Second, we should know people from Bélgica speak what languages, according to the knowledge triples, the knowledge should be (Bélgica, location.country.official_language, Dutch Language)(Bélgica, location.country.official_language, French )(Bélgica, location.country.official_language, German Language )
Refined Knowledge: (Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)\n(Bélgica, location.country.official_language, French )\n(Bélgica, location.country.official_language, German Language )

Question: Where is the college with the team South Carolina Gamecocks men's basketball team located in?
Knowledge Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )
Reasoning: First, we should know the college with the team South Carolina Gamecocks men's basketball team, which can be answered by (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball). Second, we should know where is the University of South Carolina, which is not covered by the given knowledge, however, based on my own knowledge, and the given knowledge (South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina ), it can be inferred that (University of South Carolina, location.location.containedby, South Carolina) is necessary to answer the question.
Refined Knowledge: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(University of South Carolina, location.location.containedby, South Carolina )

Question: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.cause_of_death.people, Lung Cancer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )\n(Donna Summer, people.place_of_birth.place, California)
Reasoning: First, we should know the artist that went on Live & more Encore Tour, which can be answered by (Live & More Encore Tour, music.concert_tour.artist, Donna Summer ). Second, we should know the cause of death to the Donna Summer, which can be answered by (Lung cancer, people.cause_of_death.people, Donna Summer ).
Refined Knowledge: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

Question: People from the location that appointed Adly Mansour to governmental position speak what languages?
Knowledge Triples: (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\n(Adly Mansour, people.person.nationality, Egypt)\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)
Reasoning: First, we should know the location that appointed Adly Mansour to governmental position, which is not covered by the given knowledge, however, based on my knowledge and the given knowledge (Adly Mansour, people.person.nationality, Egypt), it can be inferred that (Egypt, government.governmental.governmental_position, Adly Mansour) is necessary to answer the question. Second, we should know people from Egypt speak what language, which can be answered by (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt).
Refined Knowledge: (Egypt, government.governmental.governmental_position, Adly Mansour)\n(Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)

Question: Obama is the president of which country?
Knowledge Triples: (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America)\n(Obama, people.place_of_birth.country, America)
Reasoning: First, we should know Obama is the president of which country, which is not covered by the given knowledge, however, based on my knowledge and the given knowledge (Obama, people.place_of_birth.state, Hawaii)\n(Hawaii, location.country, America) (Obama, people.place_of_birth.country, America), it can be inferred that the knowledge (Obama, people.people_occupation.president_of, America) is necessary to answer the question.
Refined Knowledge: (Obama, people.people_occupation.president_of, America)

"""




kb_contract_prompt_dev = """Given a question and a set of knowledge triples, prune the knowledge triples according to the question. The trimed knowledge is irrelevant of the question. The remaining knowledge is necessary to answer the question.
Question: When did the champion of the 1999 World Series win their first World Series?
Knowledge Triples: (New York Yankees, sports.sports_team.championships, 1923 World Series )\n(New York Yankees, sports.sports_team.championships, 2009 World Series )\n(New York Yankees, sports.sports_team.championships, 1953 World Series )\n(New York Yankees, sports.sports_team.championships, 1950 World Series )\n(New York Yankees, sports.sports_team.championships, 1927 World Series )\n(New York Yankees, sports.sports_team.championships, 1999 World Series )\n(New York Yankees, sports.sports_team.championships, 1996 World Series )\n(New York Yankees, sports.sports_team.championships, 1951 World Series )\n(New York Yankees, sports.sports_team.championships, 1941 World Series )\n(New York Yankees, sports.sports_team.championships, 1998 World Series )\n(New York Yankees, sports.sports_team.championships, 1947 World Series )\n(New York Yankees, sports.sports_team.championships, 2000 World Series )\n(New York Yankees, sports.sports_team.championships, 1928 World Series )\n(New York Yankees, sports.sports_team.championships, 1978 World Series )\n(New York Yankees, sports.sports_team.championships, 1936 World Series )\n(New York Yankees, sports.sports_team.championships, 1962 World Series )\n(New York Yankees, sports.sports_team.championships, 1977 World Series )\n(New York Yankees, sports.sports_team.championships, 1961 World Series )\n(New York Yankees, sports.sports_team.championships, 1939 World Series )\n(New York Yankees, sports.sports_team.championships, 1937 World Series )\n(New York Yankees, sports.sports_team.championships, 1943 World Series )\n(New York Yankees, sports.sports_team.championships, 1949 World Series )\n(New York Yankees, sports.sports_team.championships, 1956 World Series )\n(New York Yankees, sports.sports_team.championships, 1952 World Series )\n(New York Yankees, sports.sports_team.championships, 1932 World Series )\n(New York Yankees, sports.sports_team.championships, 1938 World Series )\n(New York Yankees, sports.sports_team.championships, 1958 World Series )
Relevant Triples: (New York Yankees, sports.sports_team.championships, 1999 World Series)\n(New York Yankees, sports.sports_team.championships, 1923 World Series)

Question: People from the country with the capital Brussels speak what languages?
Knowledge Triples: (Bélgica, location.country.languages_spoken, Bahasa Picard )\n(Bélgica, location.country.languages_spoken, Alemany )\n(Bélgica, location.country.languages_spoken, French )\n(Bélgica, location.country.official_language, Dutch Language )\n(Bélgica, location.country.languages_spoken, Bélgican )\n(Bélgica, location.country.capital, Brussel )
Relevant Triples: (Bélgica, location.country.capital, City of Brussels)\n(Bélgica, location.country.official_language, Dutch Language)

Question: Where is the college with the team South Carolina Gamecocks men's basketball team located in?
Knowledge Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )\n(South Carolina Gamecocks men's basketball, sports.sports_team.venue, intermediate_entity_1 )\n(Colonial Life Arena, sports.sports_facility.home_venue_for, intermediate_entity_1 )\n(california, location.location.containedby, USA )\n(South Carolina Gamecocks men's basketball, sports.sports_team.arena_stadium, Colonial Life Arena )\n(South Carolina Gamecocks men's basketball, location.location.containedby, Columbia )
Relevant Triples: (University of South Carolina, education.educational_institution.sports_teams, South Carolina Gamecocks men's basketball)\n(South Carolina Gamecocks men's basketball, location.location.containedby, South Carolina )

Question: What is the cause of death to the artist that went on Live & more Encore Tour?
Knowledge Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Cancer, people.cause_of_death.people, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )
Relevant Triples: (Live & More Encore Tour, music.concert_tour.artist, Donna Summer )\n(Lung cancer, people.cause_of_death.people, Donna Summer )

Question: People from the location that appointed Adly Mansour to governmental position speak what languages?
Knowledge Triples: (Bedawi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Domari Language, language.human_language.countries_spoken_in, Egypt)\n(Arabic, Sudanese Spoken Language, language.human_language.countries_spoken_in, Egypt)\n(Adly Mansour, people.person.nationality, Egypt)\n(Nobiin Language, language.human_language.countries_spoken_in, Egypt)\n(Sa'idi Arabic, language.human_language.countries_spoken_in, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)\n(Modern Standard Arabic, language.human_language.countries_spoken_in, Egypt)\n(Arabic Language, language.human_language.countries_spoken_in, Egypt)\n(Egyptian Arabic, language.human_language.countries_spoken_in, Egypt)
Relevant Triples: (Adly Mansour, people.person.nationality, Egypt)\n(Siwi Language, language.human_language.countries_spoken_in, Egypt)

"""


kb_contract_prompt = """Given a question and a set of knowledge triples, trim the triples according to the question, the remaining triples are only necessary to answer the question.
Question: What year did the MLB franchise owned by Bill Neukom win the world series?
Knowledge Triples: (San Francisco Giants, sports.sports_team.championships, 2014 World Series )\n(2014 World Series, sports.sports_championship_event.champion, San Francisco Giants )\n(San Francisco Giants, sports.sports_team.championships, 2012 World Series )\n(2012 World Series, sports.sports_championship_event.champion, San Francisco Giants )\n(San Francisco Giants, sports.sports_team.championships, 2010 World Series )\n(2010 World Series, sports.sports_championship_event.champion, San Francisco Giants )\n(Bill Neukom, sports.sports_team_owner.teams_owned, San Francisco Giants )\n(San Francisco Giants, sports.professional_sports_team.owner_s, Bill Neukom )
Trimed Triples: (San Francisco Giants, sports.professional_sports_team.owner_s, Bill Neukom)\n(San Francisco Giants, sports.sports_team.championships, 2014 World Series)

Question: Where was the artist that had This Summer Tour raised?
Knowledge Triples: (Glen Dale, location.location.people_born_here, Brad Paisley )\n(Brad Paisley, people.person.place_of_birth, Glen Dale )\n(Beat This Summer Tour, music.concert_tour.artist, Brad Paisley )\n(Brad Paisley, music.artist.concert_tours, Beat This Summer Tour )
Trimed Triples: (Brad Paisley, music.artist.concert_tours, Beat This Summer Tour)\n(Brad Paisley, people.person.place_of_birth, Glen Dale)
 
Question: In which US county is the TV program NBC Nightside filmed in?
Knowledge Triples: (Charlotte, location.hud_county_place.county, Mecklenburg County )\n(Mecklenburg County, location.us_county.hud_county_place, Charlotte )\n(Charlotte, tv.tv_location.tv_shows_filmed_here, NBC Nightside )\n(NBC Nightside, tv.tv_program.filming_locations, Charlotte )
Trimed Triples: (Charlotte, tv.tv_location.tv_shows_filmed_here, NBC Nightside)\n(Charlotte, location.hud_county_place.county, Mecklenburg County),

Question: "What languiages are spoken by residents of the Central Western Time Zone?
Knowledge Triples:(Australia, location.country.languages_spoken, Esperanto )\n(Australia, location.country.languages_spoken, English Language )\n(Esperanto, language.human_language.countries_spoken_in, Australia )\n(Australia, location.country.languages_spoken, Lingua lojban )\n(Lingua lojban, language.human_language.countries_spoken_in, Australia )\n(Australia, location.country.languages_spoken, Anglais )\n(Anglais, language.human_language.countries_spoken_in, Australia )\n(Australia, location.location.time_zones, Central Western Time Zone )\n(Central Western Time Zone, time.time_zone.locations_in_this_time_zone, Australia )
Trimed Triples:(Australia, location.location.time_zones, Central Western Time Zone)\n(Australia, location.country.languages_spoken, English Language)
  
Question: When did the team with Crazy crab as their mascot win the world series?
Knowledge Triples:(San Francisco Giants, sports.sports_team.championships, 2014 World Series)\n(2014 World Series, sports.sports_championship_event.champion, San Frncisco Giants )\n(San Francisco Giants, sports.sports_team.championships, 2012 World Series )\n(2012 World Series, sports.sports_championship_event.champion, San Francisco Giants )\n(San Francisco Giants, sports.sports_team.championships, 2010 World Series )\n(2010 World Series, sports.sports_championship_event.champion, San Francisco Giants )\n(Crazy Crab, sports.mascot.team, San Francisco Giants )\n(San Francisco Giants, sports.sports_team.team_mascot, Crazy Crab )
Trimed Triples:(San Francisco Giants, sports.sports_team.team_mascot, Crazy Crab)\n(San Francisco Giants, sports.sports_team.championships, 2014 World Series)

"""

prompt_evaluate="""Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer whether it's sufficient for you to answer the question with these triplets and your knowledge (Yes or No).
Q: Find the person who said \"Taste cannot be controlled by law\", what did this person die from?
Knowledge Triplets: Taste cannot be controlled by law., media_common.quotation.author, Thomas Jefferson
A: {No}. Based on the given knowledge triplets, it's not sufficient to answer the entire question. The triplets only provide information about the person who said "Taste cannot be controlled by law," which is Thomas Jefferson. To answer the second part of the question, it's necessary to have additional knowledge about where Thomas Jefferson's dead.

Q: The artist nominated for The Long Winter lived where?
Knowledge Triplets: The Long Winter, book.written_work.author, Laura Ingalls Wilder
Laura Ingalls Wilder, people.person.places_lived, Unknown-Entity
Unknown-Entity, people.place_lived.location, De Smet
A: {Yes}. Based on the given knowledge triplets, the author of The Long Winter, Laura Ingalls Wilder, lived in De Smet. Therefore, the answer to the question is {De Smet}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: Steve Bisciotti, sports.professional_sports_team.owner_s, Baltimore Ravens
Steve Bisciotti, sports.sports_team_owner.teams_owned, Baltimore Ravens
Steve Bisciotti, organization.organization_founder.organizations_founded, Allegis Group
A: {No}. Based on the given knowledge triplets, the coach of the team owned by Steve Bisciotti is not explicitly mentioned. However, it can be inferred that the team owned by Steve Bisciotti is the Baltimore Ravens, a professional sports team. Therefore, additional knowledge about the current coach of the Baltimore Ravens can be used to answer the question.

Q: Rift Valley Province is located in a nation that uses which form of currency?
Knowledge Triplets: Rift Valley Province, location.administrative_division.country, Kenya
Rift Valley Province, location.location.geolocation, UnName_Entity
Rift Valley Province, location.mailing_address.state_province_region, UnName_Entity
Kenya, location.country.currency_used, Kenyan shilling
A: {Yes}. Based on the given knowledge triplets, Rift Valley Province is located in Kenya, which uses the Kenyan shilling as its currency. Therefore, the answer to the question is {Kenyan shilling}.

Q: The country with the National Anthem of Bolivia borders which nations?
Knowledge Triplets: National Anthem of Bolivia, government.national_anthem_of_a_country.anthem, UnName_Entity
National Anthem of Bolivia, music.composition.composer, Leopoldo Benedetto Vincenti
National Anthem of Bolivia, music.composition.lyricist, José Ignacio de Sanjinés
UnName_Entity, government.national_anthem_of_a_country.country, Bolivia
Bolivia, location.country.national_anthem, UnName_Entity
A: {No}. Based on the given knowledge triplets, we can infer that the National Anthem of Bolivia is the anthem of Bolivia. Therefore, the country with the National Anthem of Bolivia is Bolivia itself. However, the given knowledge triplets do not provide information about which nations border Bolivia. To answer this question, we need additional knowledge about the geography of Bolivia and its neighboring countries.

"""

generate_directly = """Q: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
A: First, the education institution has a sports team named George Washington Colonials men's basketball in is George Washington University , Second, George Washington University is in Washington D.C. The answer is {Washington, D.C.}.

Q: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
A: First, Bharoto Bhagyo Bidhata wrote Jana Gana Mana. Second, Bharoto Bhagyo Bidhata lists Pramatha Chaudhuri as an influence. The answer is {Bharoto Bhagyo Bidhata}.

Q: Who was the artist nominated for an award for You Drive Me Crazy?
A: First, the artist nominated for an award for You Drive Me Crazy is Britney Spears. The answer is {Jason Allen Alexander}.

Q: What person born in Siegen influenced the work of Vincent Van Gogh?
A: First, Peter Paul Rubens, Claude Monet and etc. influenced the work of Vincent Van Gogh. Second, Peter Paul Rubens born in Siegen. The answer is {Peter Paul Rubens}.

Q: What is the country close to Russia where Mikheil Saakashvii holds a government position?
A: First, China, Norway, Finland, Estonia and Georgia is close to Russia. Second, Mikheil Saakashvii holds a government position at Georgia. The answer is {Georgia}.

Q: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
A: First, Mitchell Lee Hedberg portrayed character Urethane Wheels Guy. Second, Mitchell Lee Hedberg overdose Heroin. The answer is {Heroin}."""

score_entity_candidates_prompt_wiki = """Please score the entities' contribution to the question on a scale from 0 to 1 (the sum of the scores of all entities is 1).
Q: Staten Island Summer, starred what actress who was a cast member of "Saturday Night Live"?
Relation: cast member
Entites: Ashley Greene; Bobby Moynihan; Camille Saviola; Cecily Strong; Colin Jost; Fred Armisen; Gina Gershon; Graham Phillips; Hassan Johnson; Jackson Nicoll; Jim Gaffigan; John DeLuca; Kate Walsh; Mary Birdsong
Score: 0.0, 0.0, 0.0, 0.4, 0.0, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4, 0.0
To score the entities\' contribution to the question, we need to determine which entities are relevant to the question and have a higher likelihood of being the correct answer.
In this case, we are looking for an actress who was a cast member of "Saturday Night Live" and starred in the movie "Staten Island Summer." Based on this information, we can eliminate entities that are not actresses or were not cast members of "Saturday Night Live."
The relevant entities that meet these criteria are:\n- Ashley Greene\n- Cecily Strong\n- Fred Armisen\n- Gina Gershon\n- Kate Walsh\n\nTo distribute the scores, we can assign a higher score to entities that are more likely to be the correct answer. In this case, the most likely answer would be an actress who was a cast member of "Saturday Night Live" around the time the movie was released.
Based on this reasoning, the scores could be assigned as follows:\n- Ashley Greene: 0\n- Cecily Strong: 0.4\n- Fred Armisen: 0.2\n- Gina Gershon: 0\n- Kate Walsh: 0.4

Q: {}
Relation: {}
Entites: """

prompt_evaluate_wiki="""Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer whether it's sufficient for you to answer the question with these triplets and your knowledge (Yes or No).
Q: Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?
Knowledge Triplets: Imperial Japanese Army, allegiance, Emperor of Japan
Yamaji Motoharu, allegiance, Emperor of Japan
Yamaji Motoharu, military rank, general
A: {Yes}. Based on the given knowledge triplets and my knowledge, Viscount Yamaji Motoharu, who was a general in the early Imperial Japanese Army, belonged to the Empire of Japan. Therefore, the answer to the question is {Empire of Japan}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: psilocybin, described by source, Opium Law,
psilocybin, found in taxon, Gymnopilus purpuratus,
psilocybin, found in taxon, Gymnopilus spectabilis, 
Opium Law, part of, norcodeine (stereochemistry defined), 
Gymnopilus purpuratus, edibility, psychoactive mushroom,
Gymnopilus spectabilis, parent taxon, Gymnopilus
A: {No}. Based on the given knowledge triplets and my knowledge, the specific psychedelic compound found in the Psilocybin genus mushroom that is converted to psilocin by the body is not explicitly mentioned. Therefore, additional knowledge about the specific compounds and their conversion to psilocin is required to answer the question.

Q: Which tennis player is younger, John Newcombe or Květa Peschke?
Knowledge Triplets: Květa Peschke, date of birth, +1975-07-09T00:00:00Z, 
John Newcombe, date of birth, +1944-05-23T00:00:00Z,
John Newcombe, country of citizenship, Australia
A: {Yes}. Based on the given knowledge triplets and my knowledge, John Newcombe was born on May 23, 1944, and Květa Peschke was born on July 9, 1975. Therefore, {Květa Peschke} is younger than John Newcombe.

Q: At what stadium did Mychal George Thompson play home games with the San Antonio Spurs?
Knowledge Triplets: San Antonio Spurs, home venue, AT&T Center
San Antonio Spurs, home venue, Alamodome
San Antonio Spurs, home venue, Fort Worth Convention Center
AT&T Center, occupant, San Antonio Spurs
Fort Worth Convention Center, located in the administrative territorial entity, Texas
Fort Worth Convention Center, occupant, San Antonio Spurs
A: {Yes}. Based on the given knowledge triplets and my knowledge, Mychal George Thompson played home games with the San Antonio Spurs at the AT&T Center. Therefore, the answer to the question is {AT&T Center}.

"""

extract_relation_prompt_wiki = """Please retrieve %s relations (separated by semicolon) that contribute to the question and rate their contribution on a scale from 0 to 1 (the sum of the scores of %s relations is 1).
Q: Mesih Pasha's uncle became emperor in what year?
Topic Entity: Mesih Pasha
Relations:
1. wiki.relation.child
2. wiki.relation.country_of_citizenship
3. wiki.relation.date_of_birth
4. wiki.relation.family
5. wiki.relation.father
6. wiki.relation.languages_spoken, written_or_signed
7. wiki.relation.military_rank
8. wiki.relation.occupation
9. wiki.relation.place_of_death
10. wiki.relation.position_held
11. wiki.relation.religion_or_worldview
12. wiki.relation.sex_or_gender
13. wiki.relation.sibling
14. wiki.relation.significant_event
A: 1. {wiki.relation.family (Score: 0.5)}: This relation is highly relevant as it can provide information about the family background of Mesih Pasha, including his uncle who became emperor.
2. {wiki.relation.father (Score: 0.4)}: Uncle is father's brother, so father might provide some information as well.
3. {wiki.relation.position held (Score: 0.1)}: This relation is moderately relevant as it can provide information about any significant positions held by Mesih Pasha or his uncle that could be related to becoming an emperor.

Q: Van Andel Institute was founded in part by what American businessman, who was best known as co-founder of the Amway Corporation?
Topic Entity: Van Andel Institute
Relations:
1. wiki.relation.affiliation
2. wiki.relation.country
3. wiki.relation.donations
4. wiki.relation.educated_at
5. wiki.relation.employer
6. wiki.relation.headquarters_location
7. wiki.relation.legal_form
8. wiki.relation.located_in_the_administrative_territorial_entity
9. wiki.relation.total_revenue
A: 1. {wiki.relation.affiliation (Score: 0.4)}: This relation is relevant because it can provide information about the individuals or organizations associated with the Van Andel Institute, including the American businessman who co-founded the Amway Corporation.
2. {wiki.relation.donations (Score: 0.3)}: This relation is relevant because it can provide information about the financial contributions made to the Van Andel Institute, which may include donations from the American businessman in question.
3. {wiki.relation.educated_at (Score: 0.3)}: This relation is relevant because it can provide information about the educational background of the American businessman, which may have influenced his involvement in founding the Van Andel Institute.

Q: """

answer_prompt_wiki = """Given a question and the associated retrieved knowledge graph triplets (entity, relation, entity), you are asked to answer the question with these triplets and your own knowledge.
Q: Viscount Yamaji Motoharu was a general in the early Imperial Japanese Army which belonged to which Empire?
Knowledge Triplets: Imperial Japanese Army, allegiance, Emperor of Japan
Yamaji Motoharu, allegiance, Emperor of Japan
Yamaji Motoharu, military rank, general
A: Based on the given knowledge triplets and my knowledge, Viscount Yamaji Motoharu, who was a general in the early Imperial Japanese Army, belonged to the Empire of Japan. Therefore, the answer to the question is {Empire of Japan}.

Q: Who is the coach of the team owned by Steve Bisciotti?
Knowledge Triplets: psilocybin, described by source, Opium Law,
psilocybin, found in taxon, Gymnopilus purpuratus,
psilocybin, found in taxon, Gymnopilus spectabilis, 
Opium Law, part of, norcodeine (stereochemistry defined), 
Gymnopilus purpuratus, edibility, psychoactive mushroom,
Gymnopilus spectabilis, parent taxon, Gymnopilus
A: Based on the given knowledge triplets and my knowledge, the specific psychedelic compound found in the Psilocybin genus mushroom that is converted to psilocin by the body is not explicitly mentioned. Therefore, additional knowledge about the specific compounds and their conversion to psilocin is required to answer the question.

Q: Which tennis player is younger, John Newcombe or Květa Peschke?
Knowledge Triplets: Květa Peschke, date of birth, +1975-07-09T00:00:00Z, 
John Newcombe, date of birth, +1944-05-23T00:00:00Z,
John Newcombe, country of citizenship, Australia
A: Based on the given knowledge triplets and my knowledge, John Newcombe was born on May 23, 1944, and Květa Peschke was born on July 9, 1975. Therefore, {Květa Peschke} is younger than John Newcombe.

Q: At what stadium did Mychal George Thompson play home games with the San Antonio Spurs?
Knowledge Triplets: San Antonio Spurs, home venue, AT&T Center
San Antonio Spurs, home venue, Alamodome
San Antonio Spurs, home venue, Fort Worth Convention Center
AT&T Center, occupant, San Antonio Spurs
Fort Worth Convention Center, located in the administrative territorial entity, Texas
Fort Worth Convention Center, occupant, San Antonio Spurs
A: Based on the given knowledge triplets and my knowledge, Mychal George Thompson played home games with the San Antonio Spurs at the AT&T Center. Therefore, the answer to the question is {AT&T Center}.

Q: {}
"""


relation_reasoning_prompt = """Given a question and some Topic Entities in the Question, output possible freebase Relation Paths starting from each Topic Entities to in order to answer the question. 
Here are some RULES you must obey:
1. Use a json dict as output format, the key of which are Topic Entities of the Question and the value of each key is an array of array, each inner array is a relation path from the Topic Entity (key) to the answer of the question.you should output different Relation Paths for each Topic Entities according to the question. The Paths are stored in an array.
2. For each topic entity, you must output at least 2 different possible relation Paths starting from this topic entity to get the final answer. The difference between the paths can be different relations or the number of relations in the path.
3. For your information, the Freebase knowledge base stores knowledge in different structures from the natural language. In other words, a relation in natural language can be represented by several (one or two or more) relations in the knowledge base. That is why I want you to output several different possible paths.
4. Please think step by step, before you output the Path.

Let me show you some examples.
#
Question: Find the person who said \"Taste cannot be controlled by law\", where did this person die from?
Topic Entities:["\"Taste cannot be controlled by law\""]
Thought: There is only one topic entity, I should output some relations paths from "\"Taste cannot be controlled by law\"" to the answer. First, I should find the person who said \"Taste cannot be controlled by law\". Second, I should find where did this person die, which is the answer.
Path: {
"\"Taste cannot be controlled by law\"":[
    ["people.person.quotations", "people.deceased_person.place_of_death"],
    ["media_common.quotation.author", "people.deceased_person.place_of_death"],
    ["quotations.quotation.author", "people.die.place_of_death"]
]
}
#
Question: Who is the director of the movie featured Miley Cyrus and was produced by Tobin Armbrust?
Topic Entities:["Miley Cyrus", "Tobin Armbrust"]\
Thought: There are two topic entities, the answer should be constrained by two relation paths. For the path starting from "Miley Cyrus", firstly, I should find the movies featured Miley Crus. Second, I should find the directors of the movies. For the path starting from "Tobin Armbrust", firstly, I should find the movies produced by Tobin Armbrust. Second, I should find the directors of the movies. Finally, the answer of the question should be the intersection of the two paths.
Path: {
"Miley Cyrus":[
    ["movies.movies.starring", "film.film.director"], 
    ["film.film.starring", "film.film_staff.director"], 
    ["film.performance.actor","film.film_maker.director"],
    ["movies.performance.actor","movies.movies.director"],
],
"Tobin Armbrust":[
    ["film.film.produced_by", "film.film.director"],
    ["movies.movies.produced_by", "film.film_maker.director"],
    ["movies.movies.executor", "film.film.director"],
    ["film.film.executor", "film.film_staff.director"],
    ["movies.movies.maker", "film.film.director"],
]
}
#
Q: The artist nominated for The Long Winter lived where?
Topic Entities:["The Long Winter lived"]
Thought: There is only one topic entity, I should output some relations paths from "The Long Winter lived" to the answer. First, I should find the artist nominated for "The Long Winter lived". Second, I should find where the artist lived, which is the answer.
Path: {
"The Long Winter lived":[
    ["book.written_work.author","people.person.places_lived","people.place_lived.location"], 
    ["award.award_nominee.award_nominations","award.award_nomination.nominated_for","people.person.places_lived","people.place_lived.location"],
    ["award.award_nomination.nominated_for","people.person.places_lived","people.place_lived.location"]
]
}
#
Q: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Topic Entities:["United Kingdom", "St. Mary's Cathedral, Batticaloa"]
Thought: There are two topic entities, the answer should be constrained by two relation paths. For the path starting from "United Kingdom", firstly, I should find major religions in "United Kingdom". For the path starting from "St. Mary's Cathedral, Batticaloa", first, I should find the religion with a place of worship named St. Mary's Cathedral, Batticaloa. Finally, the answer of the question should be the intersection of the two paths.
Path: {
"United Kingdom":[
    ["location.statistical_region.religions", "location.religion_percentage.religion"], 
    ["location.statistical_region.religions"], 
],
"St. Mary's Cathedral, Batticaloa":[
    ["religion.religious_organization.places_of_worship"]
    ["religion.religious_event.worship", "religion.religious_place.places"]
]
}
#
Q: Rift Valley Province is located in a nation that uses which form of currency?
Topic Entities:["Rift Valley Province"]
Thought: There is only one topic entity, I should output some relations paths from "Rift Valley Province" to the answer. First, I should find a nation where "Rift Valley Province" is located in. Second, I should find the form of currency used by the nation, which is the answer.
Path: {
"Rift Valley Province":[
    ["location.administrative_division.country","location.location.geolocation","location.mailing_address.state_province_region","location.country.currency_used"], 
    ["location.country.administrative_divisions","location.country.currency"],
    ["location.administrative_division.country","location.country.currency_used"]
]
}
#
Q: The country with the National Anthem of Bolivia borders which nations?
Topic Entities:["National Anthem of Bolivia"],
Thought: There is only one topic entity, I should output some relations paths from "National Anthem of Bolivia" to the answer. First, I should find the country with the national athem "National Anthem of Bolivia". Second, I should find the nations borders that country, which are the answer.
Path: {
"National Anthem of Bolivia":[
    ["government.national_anthem_of_a_country.anthem","music.composition.composer; music.composition.lyricist","government.national_anthem_of_a_country.country","location.country.national_anthem","location.adjoining_relationship.adjoins"], 
    ["location.country.national_anthem","government.national_anthem_of_a_country.anthem","location.location.adjoin_s", "location.adjoining_relationship.adjoins"],
    ["location.country.national_anthem",location.location.adjoin_s"]
]
}
#
"""


relation_reasoning_prompt_new = """Given a question and some Topic Entities in the Question, output possible freebase Relation Paths starting from each Topic Entities in order to answer the question. 
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
For, the path from "\"Taste cannot be controlled by law\"", firstly, it should cover the person quote it. Second, I should cover the place where the person died.
Path: {
"\"Taste cannot be controlled by law\"":[
    "\"Taste cannot be controlled by law\" -> people.person.quotations -> people.deceased_person.place_of_death",
    "\"Taste cannot be controlled by law\" -> media_common.quotation.author -> people.deceased_person.place_of_death",
    "\"Taste cannot be controlled by law\" -> quotations.quotation.author -> people.die.place_of_death"
]
}
#
Question: Who is the director of the movie featured Miley Cyrus and was produced by Tobin Armbrust?
Topic Entities: ["Miley Cyrus", "Tobin Armbrust"]\
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
"""



cot_prompt = """Q: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
A: First, the education institution has a sports team named George Washington Colonials men's basketball in is George Washington University , Second, George Washington University is in Washington D.C. The answer is {Washington, D.C.}.

Q: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
A: First, Bharoto Bhagyo Bidhata wrote Jana Gana Mana. Second, Bharoto Bhagyo Bidhata lists Pramatha Chaudhuri as an influence. The answer is {Bharoto Bhagyo Bidhata}.

Q: Who was the artist nominated for an award for You Drive Me Crazy?
A: First, the artist nominated for an award for You Drive Me Crazy is Britney Spears. The answer is {Jason Allen Alexander}.

Q: What person born in Siegen influenced the work of Vincent Van Gogh?
A: First, Peter Paul Rubens, Claude Monet and etc. influenced the work of Vincent Van Gogh. Second, Peter Paul Rubens born in Siegen. The answer is {Peter Paul Rubens}.

Q: What is the country close to Russia where Mikheil Saakashvii holds a government position?
A: First, China, Norway, Finland, Estonia and Georgia is close to Russia. Second, Mikheil Saakashvii holds a government position at Georgia. The answer is {Georgia}.

Q: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
A: First, Mitchell Lee Hedberg portrayed character Urethane Wheels Guy. Second, Mitchell Lee Hedberg overdose Heroin. The answer is {Heroin}."""

io_prompt = """Q: What state is home to the university that is represented in sports by George Washington Colonials men's basketball?
A: {Washington, D.C.}.

Q: Who lists Pramatha Chaudhuri as an influence and wrote Jana Gana Mana?
A: {Bharoto Bhagyo Bidhata}.

Q: Who was the artist nominated for an award for You Drive Me Crazy?
A: {Jason Allen Alexander}.

Q: What person born in Siegen influenced the work of Vincent Van Gogh?
A: {Peter Paul Rubens}.

Q: What is the country close to Russia where Mikheil Saakashvii holds a government position?
A: {Georgia}.

Q: What drug did the actor who portrayed the character Urethane Wheels Guy overdosed on?
A: {Heroin}."""




refine_prompt="""Now you are a plan refiner on a knowledge graph. Your goal is to refine the ungrounded relation path from a topic entity to reach the answer, according to some given information, to make the plan more faithful to the knowledge graph.
Here are some information provided:
1. a question
2. an initial ungrounded relation path (initial plan). The format is dict, the key of which is the starting topic entity and the value of which is an array of initial relations (ungrounded) to reach the answer of the question (information 1).
3. some already-grounded knowledge from the topic entity according to information 1. and information 2. The format is a 2-dimensional array. Each array inside, is an array (path) of triple patterns grounded in the knowledge graph, based on parts of the initial plans.
4. some possible candidates of relations linked to some nodes grounded. The format is a dict, the key of which is some grounded entities (intermediate entities in the path which is possibly relevant to the question), the value of which is relations connected to this entity. This information is given probably because the next relation in the initial plan cannot be grounded around the listed entities, so I provide you with some candidate to choose from, in order to refine the plan.
Here are some rules you must obey:
1. Your refined output plan must be in a json array format, just the same format as the input initial path. (I will show you some examples.)\
2. The given already-grounded knowledge is obtained by grounding the given initial plan relation-by-relation from a topic entity. (I will show you how by some examples) However, some relations cannot be grounded according to the plan, which means the initial plan is incorrect from this relation. You should refine the unfaithful part of the plan, so I can grounded the plan to the knowledge graph smoothly.
3. According to rule No.2, some parts of the initial ungrounded relation path can be faithful (I am able grounded to the knowledeg base). However, this does not mean that the refined one must include the grounded part. Think golbally, even though some part is correct, it does not mean this is the golden optimal path from the topic entity to the answer.
Here are some practical advice for you to refine the plan (just some advice you donnot have to choose only from these):
1. Think about whether the given initial path and the grounded knowledge is closely related to the question. Locate the part in the path and the grounded knowledge that might not be relevant, and refine the plan.
2. If the grounded knowledge is already sufficient to answer the question, this means maybe the initial plan too long. Refine it according to the question and the given knowledge.
3. If the grounded knowledge is not sufficient, and some part of the path is not grounded in the knowledge, this means something in the initial path is unfaithful. So choose a relation in the possible candidate sets and refine the plan (you can refine the whole plan, or just part of it, it depends on you).
4. If there are some knowledge in the grounded relation irrelevant to the question, there might be something wrong in the grounded part. You can decide whether to change the initial plan according to the knowledge.

Let me show you some examples.
#
Question: What major religion in the UK has a place of worship named St. Mary's Cathedral, Batticaloa?
Initial Path: {
"United Kingdom":[
    ["location.location.religions"] 
]
}
Grounded Knowledge: [[('United Kingdom','location.statistical_region.religions', 'm.047hrrd'),('United Kingdom','location.statistical_region.religions', 'm.043trcf'),('United Kingdom','location.statistical_region.religions', 'm.047hrrr'),('United Kingdom','location.statistical_region.religions', 'm.047hrqc'),('United Kingdom','location.statistical_region.religions', 'm.047hrr4'),('United Kingdom','location.statistical_region.religions', 'm.047hrr_'),('United Kingdom','location.statistical_region.religions', 'm.047hrs7'),('United Kingdom','location.statistical_region.religions', 'm.047hrsh')]]
Candidates of relations:{
    'm.047hrrd': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.043trcf': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrrr': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrqc': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrr4': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrr_': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrs7': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
    'm.047hrsh': ['rdfs.type', 'type.object.type', 'location.religion_percentage.date', 'location.religion_percentage.percentage', 'location.religion_percentage.religion']
}
Thought: According to the question, there are 2 topic entities, "United Kingdom" and "St. Mary's Cathedral, Batticaloa". The initial path starts from United Kingdom, so the goal of the path is to get the major religion in the UK. According to Grounded Knowledge and Candidates of relations, the Grounded Knowledge is not enough to answer this, they look like some cvt nodes (blank nodes) in Freebase knowledge base. Fortunately, based on Candidates of relations, I can refine the initial plan by adding a relation 'location.religion_percentage.religion', and refine the grounded relations to the faithful ones in the knowledge graph, the Refined Path is as follows.
Refined path:{
"The Long Winter lived":[
    ["location.statistical_region.religions","location.religion_percentage.religion"]
]
}
#
Question: Rift Valley Province is located in a nation that uses which form of currency?
Initial path:{
"Rift Valley Province":[
    ["place.administrative_division.country","location.location.geolocation","location.mailing_address.state_province_region","place.country.currency_used"]
]
}
Grounded Knowledge: [[('Rift Valley Province', 'location.administrative_division.country', 'Kenya'), ('Kenya', 'location.country.currency_used', 'Kenyan shilling')],[('Rift Valley Province', 'location.location.geolocation', 'm.02_pgyk'), ('m.02_pgyk', 'location.mailing_address.state_province_region', 'Rift Valley Province')],[('Rift Valley Province', 'location.mailing_address.state_province_region', 'Rift Valley Province')]]
Candidates of relations:{
    'Rift Valley': ['base.aareas.schema.administrative_area.administrative_area_type', 'base.aareas.schema.administrative_area.administrative_parent', 'base.schemastaging.context_name.pronunciation', 'kg.object_profile.prominent_type', 'location.administrative_division.country', 'location.administrative_division.fips_10_4_region_code', 'location.location.area', 'location.location.containedby', 'location.location.containedby', 'location.location.contains', 'location.location.contains', 'location.location.geolocation', 'location.location.geometry'],
    'm.02_pgyk': ['location.geocode.latitude', 'location.geocode.longitude','location.location.geolocation', 'type.type.instance']
}
Thought: According to the question, the topic entity is "Rift Valley Province". According to a path [('Rift Valley Province', 'location.administrative_division.country', 'Kenya'), ('Kenya', 'location.country.currency_used', 'Kenyan shilling')] in Grounded Knowledge, Rift Valley Province is located in Kenya, the currency used in Kenya is Kenyan shilling. So the given knowledge is sufficienct to answer the question, I can refine the relations in the Initial Path to the faithful ones in the knowledge graph, the Refined Path is as follows.
Refined path:{
"The Long Winter lived":[
    ["location.administrative_division.country","location.country.currency_used"]
]
}
#
"""

from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://127.0.0.1:3002/sparql"  # depend on your own internal address and port, shown in Freebase readme.md

# pre-defined sparqls
sparql_head_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ns:%s ?relation ?x .\n}"""
sparql_tail_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation ns:%s .\n}"""

sparql_head_relations_literal = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  %s ?relation ?x .\n}"""
sparql_tail_relations_literal = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation %s .\n}"""

sparql_head_relations_values = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tail\nWHERE {\n  %s %s ?tail .\n}"""
sparql_tail_relations_values = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation %s .\n}"""

sparql_tail_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\nns:%s ns:%s ?tailEntity .\n}""" 
sparql_tail_entities_extract_with_type = """PREFIX ns: <http://rdf.freebase.com/ns/>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nSELECT ?tailEntity\nWHERE {\nns:%s rdf:type ?tailEntity .\n}""" 
sparql_head_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\n?tailEntity ns:%s ns:%s  .\n}"""
sparql_id = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n  UNION\n  {\n    ?entity <http://www.w3.org/2002/07/owl#sameAs> ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
    
sparql_head_entities_extract_values = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\n%s %s \n ?tailEntity  %s  %s  .\n}"""
sparql_tail_entities_extract_values = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\n%s %s \n %s %s ?tailEntity .\n}""" 


def abandon_rels(relation):
    if relation == "type.object.type" or relation == "type.object.name" or relation == "type.object.key" or relation == 'type.type.instance' or relation.startswith("common.") or relation.startswith("freebase.") or relation.startswith("user.alust.default_domain.") or relation.startswith("user.avh.default_domain.") or "sameAs" in relation:
        return True
    

def execute_sparql(sparql_txt):
    sparql_txt='PREFIX : <http://rdf.freebase.com/ns/>\n'+sparql_txt
    try:
        sparql = SPARQLWrapper(SPARQLPATH)
        sparql.setQuery(sparql_txt)
        sparql.setReturnFormat(JSON)
        sparql.addExtraURITag("timeout", "10000")
        results = sparql.query().convert()

        res = []
        for x in results["results"]["bindings"]:
            res_item = {}
            for k, v in x.items():
                res_item[k] = v['value']
            res.append(res_item)
        return res
    except Exception as e:
        print(e)
        print("Freebase query error")
        print(sparql_txt)
        return []


def id2entity_name_or_type_en(entity_id):
    if entity_id.startswith("m.") == False and entity_id.startswith("g.") == False:
        return entity_id
    
    sparql_query = sparql_id % (entity_id, entity_id)
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    try:
        results = sparql.query().convert()

        if len(results["results"]["bindings"])==0:
            return entity_id
        else:
            for lines in results["results"]["bindings"]:
                if lines['tailEntity']['xml:lang']=='en':
                    return lines['tailEntity']['value']
                
            return results["results"]["bindings"][0]['tailEntity']['value']
    except:
        return entity_id


def table_result_to_list(res):
    #  把这种table的形式[{'p': 'http://rdf.freebase.com/ns/common.topic.image',
    #   's': 'http://rdf.freebase.com/ns/m.0crkzcy'},
    #  {'p': 'http://rdf.freebase.com/ns/meteorology.tropical_cyclone.tropical_cyclone_season',
    #   's': 'http://rdf.freebase.com/ns/m.06tgzm'}]
    # 转换成这种
    # {'p': ['http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
    #   'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',]
    #  's': ['http://rdf.freebase.com/ns/common.topic',
    #   'http://rdf.freebase.com/ns/common.topic']}
    if len(res)==0:
        return []
    else:
        key_list=res[0].keys()
        result={}
        for key in key_list:
            result[key]=list(set([item[key] for item in res]))
        return result
    
# print(execute_sparql("""\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity \nWHERE {\n  ns:m.0jm9h ns:location.administrative_division.country ?tailEntity .\n}"""))
# print(id2entity_name_or_type_en("m.047hrrr"))

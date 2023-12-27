from SPARQLWrapper import SPARQLWrapper, JSON

SPARQLPATH = "http://127.0.0.1:3001/sparql"  # depend on your own internal address and port, shown in Freebase folder's readme.md

# pre-defined sparqls
sparql_head_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ns:%s ?relation ?x .\n}"""
sparql_tail_relations = """\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?relation\nWHERE {\n  ?x ?relation ns:%s .\n}"""
sparql_tail_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\nns:%s ns:%s ?tailEntity .\n}""" 
sparql_tail_entities_extract_with_type = """PREFIX ns: <http://rdf.freebase.com/ns/>\nPREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>\nSELECT ?tailEntity\nWHERE {\nns:%s rdf:type ?tailEntity .\n}""" 
sparql_head_entities_extract = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT ?tailEntity\nWHERE {\n?tailEntity ns:%s ns:%s  .\n}"""
sparql_id = """PREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity\nWHERE {\n  {\n    ?entity ns:type.object.name ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n  UNION\n  {\n    ?entity <http://www.w3.org/2002/07/owl#sameAs> ?tailEntity .\n    FILTER(?entity = ns:%s)\n  }\n}"""
    
def check_end_word(s):
    words = [" ID", " code", " number", "instance of", "website", "URL", "inception", "image", " rate", " count"]
    return any(s.endswith(word) for word in words)

def abandon_rels(relation):
    if relation == "type.object.type" or relation == "type.object.name" or relation == "type.object.key" or relation == 'type.type.instance' or relation.startswith("common.") or relation.startswith("freebase.") or relation.startswith("user.alust.default_domain.") or relation.startswith("user.avh.default_domain.") or "sameAs" in relation:
        return True
    

def execute_sparql(sparql_txt):
    sparql_txt='PREFIX : <http://rdf.freebase.com/ns/>\n'+sparql_txt
    try:
        sparql = SPARQLWrapper(SPARQLPATH)
        sparql.setQuery(sparql_txt)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()

        res = []
        for x in results["results"]["bindings"]:
            res_item = {}
            for k, v in x.items():
                res_item[k] = v['value']
            res.append(res_item)
        return res
    except:
        print("Freebase query error")
        print(sparql_txt)
        return []
    

# def execurte_sparql(sparql_txt):
#     try:
#         sparql = SPARQLWrapper(SPARQLPATH)
#         sparql.setQuery(sparql_txt)
#         sparql.setReturnFormat(JSON)
#         results = sparql.query().convert()
#     except:
#         print("******************************************")
#         print("Freebase query error")
#         print(sparql_txt)
#         return []
#     return results["results"]["bindings"]


def replace_relation_prefix(relations):
    return [relation['relation']['value'].replace("http://rdf.freebase.com/ns/","") for relation in relations]

def replace_entities_prefix(entities):
    return [entity['tailEntity']['value'].replace("http://rdf.freebase.com/ns/","") for entity in entities]


def id2entity_name_or_type(entity_id):
    sparql_query = sparql_id % (entity_id, entity_id)
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if len(results["results"]["bindings"])==0:
        return "UnName_Entity"
    else:
        return results["results"]["bindings"][0]['tailEntity']['value']


def id2entity_name_or_type_en(entity_id):
    sparql_query = sparql_id % (entity_id, entity_id)
    sparql = SPARQLWrapper(SPARQLPATH)
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    if len(results["results"]["bindings"])==0:
        return entity_id
    else:
        for lines in results["results"]["bindings"]:
            if lines['tailEntity']['xml:lang']=='en':
                return lines['tailEntity']['value']
            
        return results["results"]["bindings"][0]['tailEntity']['value']



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
    
print(execute_sparql("""\nPREFIX ns: <http://rdf.freebase.com/ns/>\nSELECT DISTINCT ?tailEntity \nWHERE {\n  ns:m.0jm9h ns:location.administrative_division.country ?tailEntity .\n}"""))
# print(id2entity_name_or_type_en("m.047hrrr"))

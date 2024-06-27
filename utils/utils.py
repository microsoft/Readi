import sys, os
import datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
import json
from sentence_transformers import util
from utils.freebase_func import *
from utils.cloudgpt_aoai_new import *
import openai
import time


def readjson(file_name):
    with open(file_name, encoding='utf-8') as f:
        data = json.load(f)
    return data

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line)
            data.append(json_obj)
    return data


def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)

r_embedding_map = readjson("data/openai_embeddings/fb_relation_embed.json")


def get_openai_embedding(input_message, openai_api_keys):
    ok = False
    openai.api_key = openai_api_keys
    while not ok:
        try:
            response = openai.Embedding.create(engine="text-embedding-ada-002",
                                               input=input_message)
            ok = True
        except Exception as e:
            print(e)
            print('stuck in here get_openai_embedding')

    return response['data']


def run_llm(prompt, temperature, max_tokens, openai_api_keys, engine="gpt-35-turbo-16k-20230613"):
    got_result = False
    messages = []
    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    f = 0
    result = [{"content": ""}]
    while(f <= 5):
        try:
            response = openai.ChatCompletion.create(
                model=engine,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                frequency_penalty=0,
                presence_penalty=0,
            )

            result = response["choices"][0]['message']['content'].strip()
            if len(result) == 0:
                f += 1
                continue
            break

        except Exception as e:
            print("error: ", e)
            print("openai error, retry")

            f += 1
            # trim the input according to the model's max token limit
            if "gpt-4" in engine:
                messages[-1] = {"role":"user","content": prompt[:32767]}
                time.sleep(10)
            else:
                messages[-1] = {"role":"user","content": prompt[:16384]}
                time.sleep(5)

    return result


def get_ent_one_hop_rel(entity_id, pre_relations=[], pre_head=-1, literal=False):
    if entity_id.startswith("m.") == False and entity_id.startswith("g.")==False:
        return []
    
    sparql_relations_extract_head = sparql_head_relations % (entity_id)
    head_relations = table_result_to_list(execute_sparql(sparql_relations_extract_head))

    sparql_relations_extract_tail = sparql_tail_relations % (entity_id)
    tail_relations = table_result_to_list(execute_sparql(sparql_relations_extract_tail))

    if head_relations!=[]:
      head_relations=head_relations['relation']
      # each relation starts from ns:
      head_relations = [x.replace("http://rdf.freebase.com/ns/", "") for x in head_relations if 'http://rdf.freebase.com/ns' in x]

    # tail_relations = table_result_to_list(execute_sparql(sparql_relations_extract_tail))
    if tail_relations != []:
      tail_relations = tail_relations['relation']
      tail_relations = [x.replace("http://rdf.freebase.com/ns/", "") for x in tail_relations if 'http://rdf.freebase.com/ns' in x]

    remove_unnecessary_rel = True
    if remove_unnecessary_rel:
        head_relations = [relation for relation in head_relations if not abandon_rels(relation)]
        tail_relations = [relation for relation in tail_relations if not abandon_rels(relation)]

    if len(pre_relations) != 0 and pre_head != -1:
        head_relations = [rel for rel in pre_relations if not pre_head and rel not in head_relations]
        tail_relations = [rel for rel in pre_relations if pre_head and rel not in tail_relations]

    head_relations = list(set(head_relations))
    tail_relations = list(set(tail_relations))
    total_relations = list(set(head_relations+tail_relations))
    total_relations.sort()  # make sure the orders in prompts are always the same

    return total_relations


def entity_search(entity, relation, head=True):
    if head:
        if "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" in relation:
            tail_entities_extract = sparql_tail_entities_extract_with_type% (entity)
            entities = table_result_to_list(execute_sparql(tail_entities_extract))
        else:
            tail_entities_extract = sparql_tail_entities_extract% (entity, relation)
            entities = table_result_to_list(execute_sparql(tail_entities_extract))
    else:
        head_entities_extract = sparql_head_entities_extract% (relation, entity)
        entities = table_result_to_list(execute_sparql(head_entities_extract))

    if entities != []:
        entities = entities['tailEntity']
        entities = [x.replace("http://rdf.freebase.com/ns/", "") for x in entities if 'http://rdf.freebase.com/ns' in x]

    new_entity = [entity for entity in entities if entity.startswith("m.")]

    return new_entity


def path_to_string(path: list) -> str:
    result = ""
    for i, p in enumerate(path):
        if i == 0:
            h, r, t = p
            result += f"{h} -> {r} -> {t}"
        else:
            _, r, t = p
            result += f" -> {r} -> {t}"

    return result.strip()

def string_to_path(path_string):
    result = []
    if type(path_string) == list:
        path_string = path_string[0]
        
    path_array = path_string.split("->")
    path_array = path_array[1:]
    for lines in path_array:
        result.append(lines.strip())
    return result


def similar_search_list(question, relation_list, options):
    """Use openai embedding to filter similar relations according to the question.
    We do this because in a large-scale KG, relation_list can be very large and confuses the LLM.

    This can be optimized using cached embeddings. 
    We recommand to used cached embedding for all relations in the knowledge graph and all questions to save token.
    We do not opensource the embedding for policy reason. You can use get_openai_embedding to get the embedding to create a cache file in data/openai_embeddings and modify this function.
    
    Args:
        question 
        relation_list 
        options : providing openai_api_keys

    Returns:
        relations similar to the question
    """
    question_embedding = get_openai_embedding(question, options.openai_api_keys)[0]['embedding']
    relation_embeddings = []
    for rel in relation_list:
        if rel in r_embedding_map.keys():
            relation_embeddings.append(r_embedding_map[rel])
        else:
            relation_embeddings.append(get_openai_embedding(rel, options.openai_api_keys)[0]['embedding'])
             
    # calculate similarity between the question and relations
    similarities = util.pytorch_cos_sim(question_embedding, relation_embeddings)

    # sort relation list by similarity 
    sorted_relations = [(relation, score) for relation, score in zip(relation_list, similarities.tolist()[0])]
    sorted_relations = sorted(sorted_relations, key=lambda x: x[1], reverse=True)

    sorted_relation_list = [relation[0] for relation in sorted_relations]
    return sorted_relation_list

def get_timestamp():
    now = datetime.datetime.now()
    return now.strftime(r"%m_%d_%H_%M")


def jsonl_to_json(jsonl_file_path, json_file_path):
    data = []
    with open(jsonl_file_path, 'r') as jsonl_file:
        for line in jsonl_file:
            data.append(json.loads(line))
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4, sort_keys=False,ensure_ascii=False)

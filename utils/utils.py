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
        data=json.load(f)
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

def get_openai_embedding(input_message):
    openai.api_type = "azure"
    openai.api_base = "https://cloudgpt-openai.azure-api.net/"
    openai.api_version = "2023-07-01-preview"
    openai.api_key = get_openai_token()

    response = openai.Embedding.create(engine="text-embedding-ada-002",
                                        input=input_message)
    return response['data']


def run_llm(prompt, temperature, max_tokens, openai_api_keys, engine="gpt-35-turbo-16k-20230613"):
    openai.api_type = "azure"
    openai.api_base = "https://cloudgpt-openai.azure-api.net/"
    openai.api_version = "2023-07-01-preview"
    openai.api_key = get_openai_token()


    messages = []
    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    f = 0
    result = [{"content": ""}]
    while(f <= 5):
        try:
            response = openai.ChatCompletion.create(
                    engine=engine,
                    messages = messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0
                )
            result = response["choices"][0]['message']['content']
            if len(result) == 0:
                f += 1
                continue
            break
        except Exception as e:
            print("error: ", e)
            print("openai error, retry")

            f += 1
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
      # grailqa里没有不是ns前缀的关系，看到fb_role这些文件，CWQ也没有，看了property list，提取的有没有问题就不知道了
      # 一定得每个关系都是是ns关系
      head_relations = [x.replace("http://rdf.freebase.com/ns/", "") for x in head_relations if 'http://rdf.freebase.com/ns' in x]

    # tail_relations = table_result_to_list(execute_sparql(sparql_relations_extract_tail))
    if tail_relations!=[]:
      tail_relations=tail_relations['relation']
      tail_relations = [x.replace("http://rdf.freebase.com/ns/", "") for x in tail_relations if 'http://rdf.freebase.com/ns' in x]

    remove_unnecessary_rel = True
    if remove_unnecessary_rel:
        head_relations = [relation for relation in head_relations if not abandon_rels(relation)]
        tail_relations = [relation for relation in tail_relations if not abandon_rels(relation)]

    if len(pre_relations) !=0 and pre_head !=-1:
        head_relations = [rel for rel in pre_relations if not pre_head and rel not in head_relations]
        tail_relations = [rel for rel in pre_relations if pre_head and rel not in tail_relations]

    head_relations = list(set(head_relations))
    tail_relations = list(set(tail_relations))
    total_relations = list(set(head_relations+tail_relations))
    total_relations.sort()  # make sure the order in prompt is always equal

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

    if entities!=[]:
        # if head:
        entities=entities['tailEntity']
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
    if type(path_string)==list:
        path_string = path_string[0]
        
    path_array = path_string.split("->")
    path_array = path_array[1:]
    for lines in path_array:
        result.append(lines.strip())
    return result


def similar_search_list(question, relation_list):
    question_embedding = get_openai_embedding(question)[0]['embedding']
    relation_embeddings = []
    for rel in relation_list:
        if rel in r_embedding_map.keys():
            relation_embeddings.append(r_embedding_map[rel])
        else:
            relation_embeddings.append(get_openai_embedding(rel)[0]['embedding'])
             
    # 计算问题和每个关系的相似度
    similarities = util.pytorch_cos_sim(question_embedding, relation_embeddings)

    # 将相似度与关系列表进行配对并按相似度进行排序
    sorted_relations = [(relation, score) for relation, score in zip(relation_list, similarities.tolist()[0])]
    sorted_relations = sorted(sorted_relations, key=lambda x: x[1], reverse=True)

    # 仅返回排好序的关系列表，不包括相似度分数
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


def dedup_log(result_file_name):
    # log去重
    # 已经跑过的log都进来去个重
    if result_file_name.endswith("jsonl"):
        with open(result_file_name, 'r') as f:
            current_log_res = f.readlines()
    elif result_file_name.endswith("json"):
        current_log_res = readjson(result_file_name)
    # log去个重
    deduplication_current_log_res=[]
    done_id=[]
    for done_item in current_log_res:
        done_item=eval(done_item)
        if done_item['id'] not in done_id:
            deduplication_current_log_res.append(done_item)
            done_id.append(done_item['id'])
    # 把去过重的文件写回原文件
    if result_file_name.endswith("jsonl"):
        with open(result_file_name, 'w') as file:
            for record in deduplication_current_log_res:
                json.dump(record, file)
                file.write('\n')
    elif result_file_name.endswith("json"):
        savejson("dedup_"+result_file_name, deduplication_current_log_res)
    print('have ',len(current_log_res),' records, distinct records ', len(deduplication_current_log_res))
    return deduplication_current_log_res

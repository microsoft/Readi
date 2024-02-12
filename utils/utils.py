import sys, os
import datetime
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.prompt_list import *
import json
from rank_bm25 import BM25Okapi
from sentence_transformers import util
from sentence_transformers import SentenceTransformer
from utils.freebase_func import *
from utils.cloudgpt_aoai_new import *
import openai
import re
import time
from sentence_transformers import SentenceTransformer, util
import Levenshtein

transformer_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')


def get_openai_embedding(input_message):
    openai.api_type = "azure"
    openai.api_base = "https://cloudgpt-openai.azure-api.net/"
    openai.api_version = "2023-07-01-preview"
    openai.api_key = get_openai_token()

    response = openai.Embedding.create(engine="text-embedding-ada-002",
                                        input=input_message)

    return response['data']


def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-16k-20230613"):
    if "llama" not in engine.lower():
        openai.api_type = "azure"
        openai.api_base = "https://cloudgpt-openai.azure-api.net/"
        openai.api_version = "2023-07-01-preview"
        openai.api_key = get_openai_token()
    else:
        openai.api_key = opeani_api_keys
        openai.api_key = get_openai_token()

    # messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
    messages = []
    # rules放在这里  Q: K: A:

    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    # print("start openai")
    f = 0
    # result = ""
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
            # print(len(messages[1]["content"]))

            f += 1
            if "gpt-4" in engine:
                messages[-1] = {"role":"user","content": prompt[:32767]}
                time.sleep(10)
            else:
                messages[-1] = {"role":"user","content": prompt[:16384]}
                time.sleep(5)
    # print("end openai")
    return result



def readjson(file_name):
    with open(file_name, encoding='utf-8') as f:
        data=json.load(f)
    return data

def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            # print(line)
            json_obj = json.loads(line)
            data.append(json_obj)
    return data


def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)


def most_similar_string(input_str, string_list):
    similarity_scores = [(s, Levenshtein.distance(input_str.lower(), s.lower())) for s in string_list]
    similarity_scores.sort(key=lambda x: x[1])
    return similarity_scores[0][0]


def if_all_zero(topn_scores):
    return all(score == 0 for score in topn_scores)


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

    # entity_ids = replace_entities_prefix(entities)
    new_entity = [entity for entity in entities if entity.startswith("m.")]

    return new_entity



def all_unknown_entity(entity_candidates):
    return all(candidate == "UnName_Entity" for candidate in entity_candidates)

def del_unknown_entity(entity_candidates):
    if len(entity_candidates)==1 and entity_candidates[0]=="UnName_Entity":
        return entity_candidates
    entity_candidates = [candidate for candidate in entity_candidates if candidate != "UnName_Entity"]
    return entity_candidates



def generate_answer(question, cluster_chain_of_entities, args):
    prompt = answer_prompt + question + '\n'
    chain_prompt = '\n'.join([', '.join([str(x) for x in chain]) for sublist in cluster_chain_of_entities for chain in sublist])
    prompt += "\nKnowledge Triplets: " + chain_prompt + 'A: '
    result = run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
    return result


def save_2_jsonl(question, answer, cluster_chain_of_entities, file_name):
    dict = {"question":question, "results": answer, "reasoning_chains": cluster_chain_of_entities}
    with open("/home/v-sitaocheng/demos/llm_hallu/ToG/ToG/logs/ToG_test_50__debug{}.jsonl".format(file_name), "a") as outfile:
        json_str = json.dumps(dict)
        outfile.write(json_str + "\n")



def read_prompt(prompt_path):
    with open(prompt_path, 'r') as f:
        prompt_template = f"""{f.read()}"""
    return prompt_template

def load_jsonl(file_path):
    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def load_multiple_jsonl(file_path_list):
    data = []
    for path in file_path_list:
        data.extend(load_jsonl(path))
    return data

def list_to_string(l: list) -> str:
    prompt = '"{}"'
    return ', '.join([prompt.format(i) for i in l])


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
    path_array = path_string.split("->")
    path_array = path_array[1:]
    for lines in path_array:
        result.append(lines.strip())

    return result

class InstructFormater(object):
    def __init__(self, prompt_path):
        '''
        _summary_

        Args:
            prompt_template (_type_):
            instruct_template (_type_): _description_
        '''
        self.prompt_template = read_prompt(prompt_path)

    def format(self, instruction, message):
        return self.prompt_template.format(instruction=instruction, input=message)



def reasoning(question, cluster_chain_of_entities, args):
    prompt = prompt_evaluate + question
    chain_prompt = '\n'.join([', '.join([str(x) for x in chain]) for sublist in cluster_chain_of_entities for chain in sublist])
    prompt += "\nKnowledge Triplets: " + chain_prompt + 'A: '

    response = run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)

    result = extract_answer(response)
    if if_true(result):
        return True, response
    else:
        return False, response


def extract_answer(text):
    start_index = text.find("{")
    end_index = text.find("}")
    if start_index != -1 and end_index != -1:
        return text[start_index+1:end_index].strip()
    else:
        return ""


def if_true(prompt):
    if prompt.lower().strip().replace(" ","")=="yes":
        return True
    return False


def generate_without_explored_paths(question, args):
    prompt = generate_directly + "\n\nQ: " + question + "\nA:"
    response = run_llm(prompt, args.temperature_reasoning, args.max_length, args.opeani_api_keys, args.LLM_type)
    return response

def prepare_dataset(dataset_name):
    if dataset_name == 'cwq':
        with open('/home/v-sitaocheng/demos/llm_hallu/ToG/data/cwq.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webqsp':
        with open('../data/WebQSP.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'RawQuestion'
    elif dataset_name == 'grailqa':
        with open('../data/grailqa.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'simpleqa':
        with open('../data/SimpleQA.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'qald':
        with open('../data/qald_10-en.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'webquestions':
        with open('../data/WebQuestions.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'question'
    elif dataset_name == 'trex':
        with open('../data/T-REX.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'zeroshotre':
        with open('../data/Zero_Shot_RE.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'input'
    elif dataset_name == 'creak':
        with open('../data/creak.json',encoding='utf-8') as f:
            datas = json.load(f)
        question_string = 'sentence'
    else:
        print("dataset not found, you should pick from {cwq, webqsp, grailqa, simpleqa, qald, webquestions, trex, zeroshotre, creak}.")
        exit(-1)
    return datas[:50], question_string


def readlines(file_path):
    lines = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()  # 去除行首和行尾的空白字符
            lines.append(line)
    return lines



def similar_search_list(question, relation_list):
    question_embedding = get_openai_embedding(question)[0]['embedding']
    relation_embeddings = [i['embedding'] for i in get_openai_embedding(relation_list)]

    # # sentenceTransformer embedding
    # if sentenceTransformer_embedding:
    # question_embedding = transformer_model.encode(question, convert_to_tensor=True)
    # relation_embeddings = transformer_model.encode(relation_list, convert_to_tensor=True)

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
    return now.strftime(r"%m%d")


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


# Usage
# if __name__=='__main__':
    # jsonl_to_json('/home/v-sitaocheng/demos/results/KGQA/cwq/cwq_gpt35_init_only_onePath_CVT_HardStop_new_goal_progress_1000example__0107.jsonl', '/home/v-sitaocheng/demos/results/KGQA/cwq/cwq_gpt35_init_only_onePath_CVT_HardStop_new_goal_progress_1000example__0107.json')
    # get_ent_one_hop_rel("m.0bdxs5")
    # print_graph()

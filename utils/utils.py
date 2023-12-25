from utils.prompt_list import *
import json
from rank_bm25 import BM25Okapi
from sentence_transformers import util
from sentence_transformers import SentenceTransformer
from utils.cloudgpt_aoai_new import get_openai_token
from utils.freebase_func import *
import openai
import re
import time


def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-16k-20230613"):
    if "llama" not in engine.lower():
        # openai.api_key = "EMPTY"
        # openai.api_base = "http://localhost:8000/v1"  # your local llama server port
        # engine = openai.Model.list()["data"][0]["id"]
        
        openai.api_type = "azure"
        openai.api_base = "https://cloudgpt-openai.azure-api.net/"
        openai.api_version = "2023-07-01-preview"
        openai.api_key = get_openai_token()
    else:
        openai.api_key = opeani_api_keys
        openai.api_key = get_openai_token()

    messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
    # rules放在这里  Q: K: A:

    message_prompt = {"role":"user","content":prompt}
    messages.append(message_prompt)
    # print("start openai")
    f = 0
    result = ""
    while(f <= 5):
        try:
            response = openai.ChatCompletion.create(
                    engine=engine,
                    messages = messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0)
            result = response["choices"][0]['message']['content']
            f = 10
        except:
            print("openai error, retry")
            f += 1
            messages[-1] = {"role":"user","content": prompt[:16384]}
            print(len(messages[1]["content"]))
            time.sleep(2)
    # print("end openai")
    return result



def readjson_50(file_name):
    with open(file_name, encoding='utf-8') as f:
        data=json.load(f)
    return data


def savejson(file_name, new_data):
    with open(file_name, mode='w',encoding='utf-8') as fp:
        json.dump(new_data, fp, indent=4, sort_keys=False,ensure_ascii=False)



def retrieve_top_docs(query, docs, model, width=3):
    """
    Retrieve the topn most relevant documents for the given query.

    Parameters:
    - query (str): The input query.
    - docs (list of str): The list of documents to search from.
    - model_name (str): The name of the SentenceTransformer model to use.
    - width (int): The number of top documents to return.

    Returns:
    - list of float: A list of scores for the topn documents.
    - list of str: A list of the topn documents.
    """

    query_emb = model.encode(query)
    doc_emb = model.encode(docs)

    scores = util.dot_score(query_emb, doc_emb)[0].cpu().tolist()

    doc_score_pairs = sorted(list(zip(docs, scores)), key=lambda x: x[1], reverse=True)

    top_docs = [pair[0] for pair in doc_score_pairs[:width]]
    top_scores = [pair[1] for pair in doc_score_pairs[:width]]

    return top_docs, top_scores


def compute_bm25_similarity(query, corpus, width=3):
    """
    Computes the BM25 similarity between a question and a list of relations,
    and returns the topn relations with the highest similarity along with their scores.

    Args:
    - question (str): Input question.
    - relations_list (list): List of relations.
    - width (int): Number of top relations to return.

    Returns:
    - list, list: topn relations with the highest similarity and their respective scores.
    """

    tokenized_corpus = [doc.split(" ") for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split(" ")

    doc_scores = bm25.get_scores(tokenized_query)
    
    relations = bm25.get_top_n(tokenized_query, corpus, n=width)
    doc_scores = sorted(doc_scores, reverse=True)[:width]

    return relations, doc_scores


def clean_relations(string, entity_id, head_relations):
    pattern = r"{\s*(?P<relation>[^()]+)\s+\(Score:\s+(?P<score>[0-9.]+)\)}"
    relations=[]
    for match in re.finditer(pattern, string):
        relation = match.group("relation").strip()
        if ';' in relation:
            continue
        score = match.group("score")
        if not relation or not score:
            return False, "output uncompleted.."
        try:
            score = float(score)
        except ValueError:
            return False, "Invalid score"
        if relation in head_relations:
            relations.append({"entity": entity_id, "relation": relation, "score": score, "head": True})
        else:
            relations.append({"entity": entity_id, "relation": relation, "score": score, "head": False})
    if not relations:
        return False, "No relations found"
    return True, relations


def if_all_zero(topn_scores):
    return all(score == 0 for score in topn_scores)


def clean_relations_bm25_sent(topn_relations, topn_scores, entity_id, head_relations):
    relations = []
    if if_all_zero(topn_scores):
        topn_scores = [float(1/len(topn_scores))] * len(topn_scores)
    for relation in topn_relations:
        if relation in head_relations:
            relations.append({"entity": entity_id, "relation": relation, "score": topn_scores[i], "head": True})
        else:
            relations.append({"entity": entity_id, "relation": relation, "score": topn_scores[i], "head": False})
    return True, relations


# def run_llm(prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-20230613"):
#     if "llama" not in engine.lower():
#         openai.api_key = "EMPTY"
#         openai.api_base = "http://localhost:8000/v1"  # your local llama server port
#         # engine = openai.Model.list()["data"][0]["id"]
        
#         openai.api_type = "azure"
#         openai.api_base = "https://cloudgpt-openai.azure-api.net/"
#         openai.api_version = "2023-07-01-preview"
#         openai.api_key = get_openai_token()
#     else:
#         openai.api_key = opeani_api_keys
#         openai.api_key = get_openai_token()

#     # messages = [{"role":"system","content":"You are an AI assistant that helps people find information."}]
#     messages = []
#     message_prompt = {"role":"user","content":prompt}
#     messages.append(message_prompt)
#     print("start openai")
#     f = 0
#     while(f == 0):
#         try:
#             response = openai.ChatCompletion.create(
#                     engine=engine,
#                     messages = messages,
#                     temperature=temperature,
#                     max_tokens=max_tokens,
#                     frequency_penalty=0,
#                     presence_penalty=0)
#             result = response["choices"][0]['message']['content']
#             f = 1
#         except:
#             print("openai error, retry")
#             print(messages)
#             time.sleep(2)
#     print("end openai")
#     return result

def construct_relation_prune_prompt(question, entity_name, total_relations, args):
    return extract_relation_prompt % (args.width, args.width) + question + '\nTopic Entity: ' + entity_name + '\nRelations: '+ '; '.join(total_relations) + "\nA: "
        

def construct_entity_score_prompt(question, relation, entity_candidates, score):
    return score_entity_candidates_prompt.format(question, relation) + "; ".join(entity_candidates) + '\nScore: ' + str(score)


def get_ent_one_hop_rel(entity_id, pre_relations=[], pre_head=-1):
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

def relation_search_prune(entity_id, entity_name, pre_relations, pre_head, question, args):
    sparql_relations_extract_head = sparql_head_relations % (entity_id)
    head_relations = execute_sparql(sparql_relations_extract_head)
    head_relations = replace_relation_prefix(head_relations)
    
    sparql_relations_extract_tail= sparql_tail_relations % (entity_id)
    tail_relations = execute_sparql(sparql_relations_extract_tail)
    tail_relations = replace_relation_prefix(tail_relations)

    if args.remove_unnecessary_rel:
        head_relations = [relation for relation in head_relations if not abandon_rels(relation)]
        tail_relations = [relation for relation in tail_relations if not abandon_rels(relation)]
    
    if len(pre_relations)!=0 and pre_head !=-1:
        tail_relations = [rel for rel in pre_relations if pre_head and rel not in tail_relations]
        head_relations = [rel for rel in pre_relations if not pre_head and rel not in head_relations]

    head_relations = list(set(head_relations))
    tail_relations = list(set(tail_relations))
    total_relations = head_relations+tail_relations
    total_relations.sort()  # make sure the order in prompt is always equal
    
    if args.prune_tools == "llm":
        prompt = construct_relation_prune_prompt(question, entity_name, total_relations, args)

        result = run_llm(prompt, args.temperature_exploration, args.max_length, args.opeani_api_keys, args.LLM_type)
        flag, retrieve_relations_with_scores = clean_relations(result, entity_id, head_relations) 

    elif args.prune_tools == "bm25":
        topn_relations, topn_scores = compute_bm25_similarity(question, total_relations, args.width)
        flag, retrieve_relations_with_scores = clean_relations_bm25_sent(topn_relations, topn_scores, entity_id, head_relations) 
    else:
        model = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
        topn_relations, topn_scores = retrieve_top_docs(question, total_relations, model, args.width)
        flag, retrieve_relations_with_scores = clean_relations_bm25_sent(topn_relations, topn_scores, entity_id, head_relations) 

    if flag:
        return retrieve_relations_with_scores
    else:
        return [] # format error or too small max_length
    
    
def entity_search(entity, relation, head=True):
    if head:
        if "http://www.w3.org/1999/02/22-rdf-syntax-ns#type" in relation:
            tail_entities_extract = sparql_tail_entities_extract_with_type% (entity)
            entities = table_result_to_list(execute_sparql(tail_entities_extract)) 
        else:
            tail_entities_extract = sparql_tail_entities_extract% (entity, relation)
            entities = table_result_to_list(execute_sparql(tail_entities_extract))
    else:
        head_entities_extract = sparql_head_entities_extract% (entity, relation)
        entities = table_result_to_list(execute_sparql(head_entities_extract))

    if entities!=[]:
        # if head:
        entities=entities['tailEntity']
        entities = [x.replace("http://rdf.freebase.com/ns/", "") for x in entities if 'http://rdf.freebase.com/ns' in x]

    # entity_ids = replace_entities_prefix(entities)
    new_entity = [entity for entity in entities if entity.startswith("m.")]
    
    return new_entity


def entity_score(question, entity_candidates_id, score, relation, args):
    entity_candidates = [id2entity_name_or_type(entity_id) for entity_id in entity_candidates_id]
    if all_unknown_entity(entity_candidates):
        return [1/len(entity_candidates) * score] * len(entity_candidates), entity_candidates, entity_candidates_id
    entity_candidates = del_unknown_entity(entity_candidates)
    if len(entity_candidates) == 1:
        return [score], entity_candidates, entity_candidates_id
    if len(entity_candidates) == 0:
        return [0.0], entity_candidates, entity_candidates_id
    
    # make sure the id and entity are in the same order
    zipped_lists = sorted(zip(entity_candidates, entity_candidates_id))
    entity_candidates, entity_candidates_id = zip(*zipped_lists)
    entity_candidates = list(entity_candidates)
    entity_candidates_id = list(entity_candidates_id)
    if args.prune_tools == "llm":
        prompt = construct_entity_score_prompt(question, relation, entity_candidates, score)

        result = run_llm(prompt, args.temperature_exploration, args.max_length, args.opeani_api_keys, args.LLM_type)
        return [float(x) * score for x in clean_scores(result, entity_candidates)], entity_candidates, entity_candidates_id

    elif args.prune_tools == "bm25":
        topn_entities, topn_scores = compute_bm25_similarity(question, entity_candidates, args.width)
    else:
        model = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
        topn_entities, topn_scores = retrieve_top_docs(question, entity_candidates, model, args.width)
    if if_all_zero(topn_scores):
        topn_scores = [float(1/len(topn_scores))] * len(topn_scores)
    return [float(x) * score for x in topn_scores], topn_entities, entity_candidates_id

    
def all_unknown_entity(entity_candidates):
    return all(candidate == "UnName_Entity" for candidate in entity_candidates)

def del_unknown_entity(entity_candidates):
    if len(entity_candidates)==1 and entity_candidates[0]=="UnName_Entity":
        return entity_candidates
    entity_candidates = [candidate for candidate in entity_candidates if candidate != "UnName_Entity"]
    return entity_candidates

def clean_scores(string, entity_candidates):
    scores = re.findall(r'\d+\.\d+', string)
    scores = [float(number) for number in scores]
    if len(scores) == len(entity_candidates):
        return scores
    else:
        print("All entities are created equal.")
        return [1/len(entity_candidates)] * len(entity_candidates)

def update_history(entity_candidates, entity, scores, entity_candidates_id, total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities, total_head):
    if len(entity_candidates) == 0:
        entity_candidates.append("[FINISH]")
        entity_candidates_id = ["[FINISH_ID]"]
    candidates_relation = [entity['relation']] * len(entity_candidates)
    topic_entities = [entity['entity']] * len(entity_candidates)
    head_num = [entity['head']] * len(entity_candidates)
    total_candidates.extend(entity_candidates)
    total_scores.extend(scores)
    total_relations.extend(candidates_relation)
    total_entities_id.extend(entity_candidates_id)
    total_topic_entities.extend(topic_entities)
    total_head.extend(head_num)
    return total_candidates, total_scores, total_relations, total_entities_id, total_topic_entities, total_head


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


def entity_prune(total_entities_id, total_relations, total_candidates, total_topic_entities, total_head, total_scores, args):
    zipped = list(zip(total_entities_id, total_relations, total_candidates, total_topic_entities, total_head, total_scores))
    sorted_zipped = sorted(zipped, key=lambda x: x[5], reverse=True)
    sorted_entities_id, sorted_relations, sorted_candidates, sorted_topic_entities, sorted_head, sorted_scores = [x[0] for x in sorted_zipped], [x[1] for x in sorted_zipped], [x[2] for x in sorted_zipped], [x[3] for x in sorted_zipped], [x[4] for x in sorted_zipped], [x[5] for x in sorted_zipped]

    entities_id, relations, candidates, topics, heads, scores = sorted_entities_id[:args.width], sorted_relations[:args.width], sorted_candidates[:args.width], sorted_topic_entities[:args.width], sorted_head[:args.width], sorted_scores[:args.width]
    merged_list = list(zip(entities_id, relations, candidates, topics, heads, scores))
    filtered_list = [(id, rel, ent, top, hea, score) for id, rel, ent, top, hea, score in merged_list if score != 0]
    if len(filtered_list) ==0:
        return False, [], [], [], []
    entities_id, relations, candidates, tops, heads, scores = map(list, zip(*filtered_list))

    tops = [id2entity_name_or_type(entity_id) for entity_id in tops]
    cluster_chain_of_entities = [[(tops[i], relations[i], candidates[i]) for i in range(len(candidates))]]
    return True, cluster_chain_of_entities, entities_id, relations, heads



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

def rule_to_string(rule: list, sep_token = "<SEP>", bop = "<PATH>", eop = "</PATH>") -> str:
    if len(rule) == 1:
        rule_string = rule[0]
    else:
        rule_string = sep_token.join(rule)
    return bop + rule_string + eop

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

def half_stop(question, cluster_chain_of_entities, args):
    print("No new knowledge added during search depth %d, stop searching." % args.depth)
    answer = generate_answer(question, cluster_chain_of_entities, args)
    save_2_jsonl(question, answer, cluster_chain_of_entities, file_name=args.dataset)


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


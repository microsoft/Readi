import sys
import os
from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np
from config import LLM_BASE
import json
import random
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.utils import run_llm, get_timestamp, readjson
from utils.freebase_func import *
import time
from tqdm import tqdm
from utils import *
from config import *
from kg_instantiation import *
import tiktoken

PROMPT_PATH = "prompt/kgqa"

def parse_args():
    parser = ArgumentParser("KGQA for cwq or WebQSP")
    parser.add_argument("--full", action="store_true", help="full dataset.")
    parser.add_argument("--verbose", action="store_true", help="verbose or not.", default=False)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=1024)
    parser.add_argument("--max_token_reasoning", type=int, default=2048)
    parser.add_argument("--max_que", type=int, default=200)
    parser.add_argument("--dataset", type=str, required=True, help="choose the dataset.choices={\"cwq\", \"WebQSP\"}")
    parser.add_argument("--llm", type=str, choices=LLM_BASE.keys(), default="gpt35", help="base LLM model.")
    parser.add_argument("--openai_api_keys", type=str, help="opeani_api_keys", default="", required=True)
    parser.add_argument("--count_token_cost", type=bool, help="count_token_cost", default=False)
    parser.add_argument("--initial_path_eval", type=bool, help="evaluate initial reasoning path (ablation study)", default=False)
    
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args


def question_process(fpath):
    if fpath.endswith('jsonl'):
        data = read_jsonl(fpath)
    else:
        data = readjson(fpath)

    return data


def num_tokens_from_string(string: str, model_name: str = "gpt-3.5-turbo") -> int:
    """Returns the number of tokens in a text string.  For calculating token cost."""
    encoding = tiktoken.encoding_for_model(model_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def LLM_edit(reasoning_path_LLM_init, entity_label, feedback, question, options, input_token_cnt=0, output_token_cnt=0):
    """
    reasoning path editing

    Args:
        reasoning_path_LLM_init : previous reasoning path
        entity_label : topic entity
        feedback : prepared error message for editing
        question 
        options 
        input_token_cnt 
        output_token_cnt

    Returns:
        reasoning_path_LLM_init : edited reasoning path
        thought : LLM CoT
        input_token_cnt, output_token_cnt : to calculate token cost
    """
    init_path = reasoning_path_LLM_init[entity_label]
    err_msg, grounded_know_string, candidate_rel = feedback

    prompt = open(
        os.path.join(PROMPT_PATH, f"{options.dataset}_edit.md"),
        'r', encoding='utf-8'
    ).read()

    prompts = prompt + "Question: " + question + "\nInitial Path: " + str(init_path) + "\n>>>> Error Message\n" + err_msg + ">>>> Instantiation Context\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel)  + "\n>>>> Corrected Path\nGoal: "

    for _ in range(MAX_LLM_RETRY_TIME):
        try:
            response = run_llm(prompts, temperature=options.temperature, max_tokens=options.max_token, openai_api_keys=options.openai_api_keys, engine=options.LLM_type)

            new_path = response.split("Final Path:")[-1].strip().strip("\"").strip()
            thought = response
            if entity_label not in new_path or "->" not in new_path:
                raise ValueError("entity_label or -> is not in path")
            
            if new_path == init_path:
                raise ValueError("no changing origin plan")

            if "->" not in new_path or entity_label not in new_path:
                raise ValueError("output empty plan or without the starting point")

            elements = new_path.split(" -> ")
            if len(list(set(elements))) < len(elements):
                raise ValueError("same relation in path")
            
            if len(elements) > 5:
                raise ValueError("path too long!!!!")

            reasoning_path_LLM_init[entity_label] = new_path
            break
        except Exception as e:
            if options.verbose:
                error_line = "*" * 40
                print(error_line)
                print(e)
                print("---------- new path -----------:", new_path)
                print(error_line)
                print()
            time.sleep(1)
            
    if options.count_token_cost:
        input_token_cnt += num_tokens_from_string(prompt)
        output_token_cnt += num_tokens_from_string(response)
    
    return reasoning_path_LLM_init, thought, input_token_cnt, output_token_cnt

def get_init_reasoning_path(question, topic_ent, options, input_token_cnt=0, output_token_cnt=0):
    """generate initial reasoning path

    Args:
        question
        topic_ent : topic entities
        options : parsed arguments
        input_token_cnt : to calculate token cost
        output_token_cnt : to calculate token cost

    Returns:
        init_reasoning_path
        input_token_cnt
        output_token_cnt
    """
    prompt = open(
        os.path.join(PROMPT_PATH, f"{options.dataset}_init.md"),
        'r', encoding='utf-8'
    ).read()
    
    # default empty path
    default_relation_path = {
        k: k
        for k in topic_ent
    } 
    
    prompt += "Question: " + question + "\nTopic Entities:" + str(topic_ent)+ "\nThought:"
    init_reasoning_path = default_relation_path
    
    for _ in range(MAX_LLM_RETRY_TIME):
        try:
            response = run_llm(prompt, options.temperature, options.max_token_reasoning, options.openai_api_keys, options.LLM_type)

            reponse_dict = eval(response.split("Path:")[-1].strip())
            for k, v in reponse_dict.items():
                if type(v) == list:
                    init_reasoning_path[k]=v[0]         
            assert type(init_reasoning_path) == dict   
            break
        
        except Exception as e:
            init_reasoning_path = default_relation_path
            print(e)
            error_line = "*" * 40
            print(response)
            time.sleep(1)
            print(error_line)
    
    if options.count_token_cost:
        input_token_cnt += num_tokens_from_string(prompt)
        output_token_cnt += num_tokens_from_string(response)
    
    return init_reasoning_path, input_token_cnt, output_token_cnt


def llm_reasoning(reasoning_paths_instances, question, options):
    """call llm for QA reasoning"""
    kg_instances_str = ""
    kg_triple_set = []
    response = ""
    
    prompt = open(
        os.path.join(PROMPT_PATH, f"kgqa_reasoning.md"),
        'r', encoding='utf-8'
    ).read()
    
    cot_prompt = open(
        os.path.join(PROMPT_PATH, "cot_reasoning.md"),
        'r', encoding='utf-8'
    ).read()
    
    for lines in reasoning_paths_instances:
        for l in lines:
            triple = [l[0] , l[1] , l[2]]
            if triple not in kg_triple_set:
                kg_triple_set.append(triple)

    for l in kg_triple_set:
        kg_instances_str += "(" + l[0] + ", " + l[1] + ", " + l[2] + " )\n"
    kg_instances_str = kg_instances_str.strip("\n")   
    
    if len(kg_instances_str) > 0:
        prompts = prompt + "Q: " + question + "\nKnowledge Triplets: " + kg_instances_str + "\nA: "
        for _ in range(MAX_LLM_RETRY_TIME):
            try:
                response = run_llm(prompts, options.temperature, options.max_token, options.openai_api_keys, options.LLM_type)
                
                if len(response) == 0:
                    print(f"\n{'*'*10} Empty Results {'*'*10}")
                    print("Q: " + question)
                    print("*"*30 + '\n')
                    continue

                if "{" not in response or "}" not in response:
                    print(f"\n{'*'*10} Invalid Results {'*'*10}")
                    print(response)
                    print()
                    continue
                else:
                    break
            except Exception as e:
                continue
    
    # use internal knowledge if failed too many times
    if "{" not in response or "}" not in response or len(kg_instances_str) == 0 or len(response) == 0:
        prompts = cot_prompt + "Q: " + question + "\nA: "
        response = run_llm(prompts, options.temperature, options.max_token, options.openai_api_keys, options.LLM_type)

    return response

def check_string(string):
    return "{" in string

def clean_results(string):
    """
    Extract result from LLM output.

    Args:
        string : LLM output

    Returns:
        extracted result
    """
    if "{" in string:
        start = string.find("{") + 1
        end = string.find("}")
        content = string[start:end]
        return content
    else:
        return "NULL"
   
def hit1(response, answers):
    clean_result = response.strip().replace(" ","").lower()
    for answer in answers:
        clean_answer = answer.strip().replace(" ","").lower()
        # the line below is used by ToG
        # if clean_result == clean_answer or clean_result in clean_answer or clean_answer in clean_result:
        if clean_result == clean_answer or clean_answer in clean_result:
            return True
    return False 

def evaluate(results, ground_truth):
    """return hit"""
    hit = 0
    if check_string(results):
        response = clean_results(results)
        if type(response) != str:
            response=""
        if response=="NULL":
            response = results
        else:
            if response != "" and hit1(response, ground_truth):
                hit=1
    else:
        response = results
        if type(response) != str:
            response = ""
        if response != "" and hit1(response, ground_truth):
            hit = 1
    return hit

def check_ending(result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict, reasoning_path_LLM_init, entity_label, question, options):
    """
    Check if we need to edit the reasoning path.
    If so, prepare the feedback from instantiation information.

    Args:
        result_paths : KG instances
        grounded_knowledge_current : stores all instances during BFS (length starting from 0)
        ungrounded_neighbor_relation_dict : if instantiation fails, this store some relations as candidates for editing
        reasoning_path_LLM_init : previous reasoning path from each topic entity
        entity_label : topic entity
        question 
        options

    Returns:
        max_path_len : length for the longest instance
        End_loop_cur_path: whether we need to edit the reasoning path
        (err_msg, grounded_know_string, candidate_rel) : prepared feedback for editing
    """
    
    max_path_len = grounded_knowledge_current[-1][-1]
    init_path = reasoning_path_LLM_init[entity_label]
    grounded_know = []
    ungrounded_cand_rel = {}
    max_grounded_len = 0
    cvt_ending = False
    
    if options.verbose:
        print("max len of grounded knowledge current: ", max_path_len)
    End_loop_cur_path = True

    # check if anything goes wrong and get the reasoning
    if len(result_paths) > 0:
        if max_path_len == 0:
            End_loop_cur_path = False

        for path in result_paths:
            if len(path) < max_path_len:
                continue
            # check if cvt node ending for Freebase (m. g.)
            if path[-1][-1].startswith("m.") or path[-1][-1].startswith("g."):
                End_loop_cur_path=False
                break
    else:
        End_loop_cur_path = False

    if len(grounded_knowledge_current) > 0:
        max_grounded_len = grounded_knowledge_current[-1][-1]

    # process grounded knowledge (some relations might be instantiated successfully)  - code below can be optional if we do not need to edit the path
    for know in grounded_knowledge_current:
        node_label = utils.id2entity_name_or_type_en(know[0])
        
        if node_label.startswith("m.") == False and know[2] != 0 and know[2] == max_grounded_len:
            if node_label in ungrounded_neighbor_relation_dict.keys():
                ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
            grounded_know.append(know[1])
            
        if know[2] == max_grounded_len and node_label.startswith("m."):
            cvt_ending = True

    # 15 is a hyper parameter to prevent too much knowledge in LLM context
    grounded_know = grounded_know if len(grounded_know) <= 15 else random.sample(grounded_know, 15)

    # process all cvt nodes into <cvt></cvt>
    cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0 and i[2]==max_grounded_len]
    # cvt_know = list(set(cvt_know))
    # 10 is a hyper parameter to prevent too much knowledge in LLM context
    cvt_know = cvt_know if len(cvt_know) <= 10 else random.sample(cvt_know, 10)

    for cvt in cvt_know:
        if cvt[0] in ungrounded_neighbor_relation_dict.keys():
            # the label of a cvt node is the original mid
            ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
        grounded_know.append(cvt[1])

    grounded_know = [" -> ".join([i if not i.startswith("m.") else "<cvt></cvt>" for i in utils.path_to_string(knowledge).split(" -> ")]) for knowledge in grounded_know]
    grounded_know = list(set(grounded_know))
    grounded_know_string = "\n".join(grounded_know)

    if len(grounded_know) == 0 and len(ungrounded_neighbor_relation_dict) > 0:
        ungrounded_cand_rel = ungrounded_neighbor_relation_dict

    # prepare candidate relations
    candidate_rel = []
    for k, v in ungrounded_cand_rel.items():
        candidate_rel.extend(v)
    candidate_rel = list(set(candidate_rel))

    # filter similar relations as candidates. 35 is a hyper parameter to prevent too much knowledge in LLM context
    candidate_rel = candidate_rel if len(candidate_rel) <= 35 else utils.similar_search_list(question, candidate_rel, options)[:35]
    candidate_rel.sort()

    # prepare error message for editing
    err_msg_list = []
    if cvt_ending:
        err_msg_list.append("<cvt></cvt> in the end.")
    if "->" not in init_path:
        err_msg_list.append("Empty Initial Path.")
    else:
        relation_elements = init_path.split(" -> ")[1:]
        if max_grounded_len < len(relation_elements):
            ungrounded_relation = relation_elements[max_grounded_len]
            err_msg_list.append(f"relation \"{ungrounded_relation}\" not instantiated.")
            
    err_msg = ""
    for index, msg in enumerate(err_msg_list):
        err_msg += str(index+1)+". "+ msg +"\n"

    return max_path_len, End_loop_cur_path, (err_msg, grounded_know_string, candidate_rel)

def merge_different_path(grounded_revised_knowledge, reasoning_paths, options):
    """
    Merge different paths instances from different topic entities.
    For instances from each topic entity, we first take all entities in these instances and calculate the intersection of these entities.
    If the intersection is not empty, we retain all instances containing these intersected entities for instances from each topic entities.
    For example, for the question "What country bordering France contains an airport that serves Nijmegen?", we have instances from "France" and "Nijmegen".
    We take all entities from "France" and "Nijmegen" and calculate that the intersection is "German".
    Then, we retain all path instances for "France" and "Nijmegen" containing "German".

    Moreover, if one path instances contains too much instances (more than 50), we remove some these instances, because they might not be useful for LLM's QA reasoning.

    Args:
        grounded_revised_knowledge : knowledge instances from each topic entity
        reasoning_paths : all knowledge instances (cumulated)
        options

    Returns:
        merged path instances
    """
    if options.verbose:
        print("**********************merge*****************************")
    
    # get related entities and knowledge length for each topic entity
    entity_sets={}
    knowledeg_len_dict={}
    for topic_entity, grounded_knowledge in grounded_revised_knowledge.items():
        if not topic_entity in entity_sets.keys():
            entity_sets[topic_entity]=set()

        knowledge_len = 0
        for paths in grounded_knowledge:
            knowledge_len += len(paths)
            for triples in paths:
                entity_sets[topic_entity].add(triples[0])
                entity_sets[topic_entity].add(triples[2])
        knowledeg_len_dict[topic_entity] = knowledge_len

    intersec_set = ""
    for topic_entity, entities_in_knowledge in entity_sets.items():
        if type(intersec_set) == str:
            intersec_set = entities_in_knowledge
        else:
            intersec_set = intersec_set.intersection(entities_in_knowledge)
            # take intersection according to intersected entities
            if len(intersec_set) > 0:
                new_reasoning_paths = []
                lists_of_paths = []
                for path in reasoning_paths:
                    for i in intersec_set:
                        if i in str(path):
                            new_reasoning_paths.append(path)
                            lists_of_paths.append(utils.path_to_string(path))
                reasoning_paths = new_reasoning_paths
            else:
                # no intersection, and the current path contains too much instances (which might not be useful)
                if len(reasoning_paths) > 30:
                    for k, v in knowledeg_len_dict.items():
                        if v > 50:
                            new_reasoning_paths = []
                            lists_of_paths = []
                            for path in reasoning_paths:
                                string_path = str(path).strip("[").strip("(").strip("\'").strip("\"").strip()
                                if not string_path.startswith(k):
                                    new_reasoning_paths.append(path)
                                    lists_of_paths.append(utils.path_to_string(path))
                            reasoning_paths = new_reasoning_paths

    return reasoning_paths

def main():    
    options.LLM_type = LLM_BASE[options.llm]
    input_file = get_dataset_file(options.dataset)
    output_file = os.path.join(OUTPUT_FILE_PATH, f"KGQA/{options.dataset}_{options.llm}_{get_timestamp()}.jsonl")
    question_string = get_question_string(options.dataset)
    dataset = question_process(input_file)
    input_token_cnt = 0
    output_token_cnt = 0
    
    print("save output file to: ", output_file)    
    if not options.full:
        dataset = dataset

    metrics = {
        'hit':[],
        'token_cost':[],
        'init_path_hit':[]
    }

    f = open(output_file, 'w+', encoding='utf-8')
    
    for index, item in enumerate(tqdm(dataset)):
        topic_ent_list = get_topic_entity_list(item, input_file)
        topic_ent_dict = get_topic_entity_dict(item, input_file)
        
        # skip for items without a topic entity
        if topic_ent_list == []:
            print(f"Sample {index}: topic entity is empty, sample: {item}")
            # this is critical. Please check if you need to continue
            continue
        
        question = item[question_string] if not item[question_string].endswith('?') else item[question_string] + '?'
        ground_truth = get_ground_truth(item, options.dataset)

        # reasoning path generation
        init_reasoning_path, input_token_cnt, output_token_cnt = get_init_reasoning_path(question, topic_ent_list, options, input_token_cnt, output_token_cnt)
        
        if options.verbose:
            print(f"Question:{question}")
            print(f"init reasoning path: {init_reasoning_path}")
        refine = 0

        # kg instance for each path from the topic entity
        knowledge_instance_final = dict.fromkeys(topic_ent_list, [])
        len_of_grounded_knowledge = dict.fromkeys(topic_ent_list, [])
        len_of_predict_knowledge = dict.fromkeys(topic_ent_list, [])
        reasoning_paths = []
        thought = ""
        lists_of_paths = []
        predict_path = dict.fromkeys(topic_ent_list, [])
    
        # instantitation for each path
        for entity_id, entity_label in topic_ent_dict.items():
            if entity_label not in init_reasoning_path.keys():
                continue
            
            if options.verbose:
                print("Topic entity: ", entity_label)
            
            while refine < MAX_REFINE_TIME:
                # relation binding
                binded_relations = relation_binding(init_reasoning_path, topk=5)
                relation_path_array = utils.string_to_path(init_reasoning_path[entity_label])
                sequential_relation_candidates = [binded_relations[relation] for relation in relation_path_array]
                
                # path connecting for each path
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = bfs_for_each_path(entity_id, relation_path_array, sequential_relation_candidates, options, options.max_que)
                
                # check if we need to edit the reasoning path
                max_path_len, end_refine, feedback = check_ending(result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict, init_reasoning_path, entity_label, question, options)
                
                # store length of predicted and grounded knowledge. These information can be used for reasoning path analysis
                len_of_predict_knowledge[entity_label].append(len(init_reasoning_path[entity_label].split("->"))-1)
                len_of_grounded_knowledge[entity_label].append(max_path_len)    
                predict_path[entity_label].append(init_reasoning_path[entity_label])

                if options.verbose:
                    print("len of predict path", len(init_reasoning_path[entity_label].split("->"))-1)    

                # test init reasoning path
                if options.initial_path_eval and refine == 0:
                    reasoning_paths_init = []
                    reasoning_paths_init.extend(result_paths)
                    # llm QA reasoning
                    response_init = llm_reasoning(reasoning_paths_init, question, options)
                    hit_init = evaluate(response_init, ground_truth)
                    metrics['init_path_hit'].append(hit_init)
                    print(f"hit_init:{np.mean(metrics['init_path_hit'])}")               
                    
                # invoke editing
                if not end_refine:   
                    refine += 1
                    init_reasoning_path, thought, input_token_cnt, output_token_cnt = LLM_edit(init_reasoning_path, entity_label, feedback, question, options, input_token_cnt, output_token_cnt)
                    if options.verbose:
                        print(f"{f'feedback: {feedback}' if not end_refine else ''}")
                        print(f"Refine time:{refine}")
                
                # no more editing, post process of this path
                if end_refine or refine >= MAX_REFINE_TIME-1:
                    reasoning_paths.extend(result_paths)
                    knowledge_instance_final[entity_label] = result_paths
                    lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]

                    if max_path_len > 0:
                        for grounded_path in grounded_knowledge_current:
                            if grounded_path[-1] < max_path_len:
                                continue
                            string_path = utils.path_to_string(grounded_path[1])
                            if len(string_path) > 0:
                                if string_path not in lists_of_paths:
                                    lists_of_paths.append(string_path)

                                    if len(reasoning_paths) == 0:
                                        reasoning_paths = [grounded_path[1]]
                                    else:
                                        reasoning_paths.extend([grounded_path[1]])
                        lists_of_paths = list(set(lists_of_paths))
                    break
           
        # merge kg instances for each path
        if len(topic_ent_list) > 1:
                reasoning_paths = merge_different_path(knowledge_instance_final, reasoning_paths, options)

        # llm QA reasoning
        response = llm_reasoning(reasoning_paths, question, options)
        hit = evaluate(response, ground_truth)
        token_cost = (0.0015 * input_token_cnt + 0.002 * output_token_cnt) / 1000
        info = {
            'question':question,
            'init_path': init_reasoning_path,
            'predict': response,
            'ground_truth': ground_truth,
            'kg_instances': reasoning_paths,
            'thought': thought,
            'hit':hit,
        }
        d = json.dumps(info)
        f.write(d + '\n')

        metrics["hit"].append(hit)
        metrics['token_cost'].append(token_cost)
        print(f"hit:{np.mean(metrics['hit'])}")
        # print(f"cost:{np.mean(metrics['token_cost'])}")

    f.close()
    print("\n" + "*" * 20 + "\n")
    print(f"hit:{np.mean(metrics['hit'])}")

if __name__ == '__main__':
    options = parse_args()
    main()

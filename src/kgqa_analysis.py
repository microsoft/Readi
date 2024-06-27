import sys, os, string, re
from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np
from config import LLM_BASE
import json
import random
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.utils import get_timestamp
from utils.freebase_func import *
from tqdm import tqdm
from utils import *
from config import *
from kg_instantiation import *
from kgqa import *

PROMPT_PATH = "prompt/kgqa"

def parse_args():
    parser = ArgumentParser("kgqa analysis for cwq")
    parser.add_argument("--full", action="store_true", help="full dataset.")
    parser.add_argument("--verbose", action="store_true", help="verbose or not.", default=True)
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=2048)
    parser.add_argument("--max_token_reasoning", type=int, default=4096)
    parser.add_argument("--max_que", type=int, default=150)
    parser.add_argument("--analysis_strategy", type=str, choices={"llm_refine", "init_only", "init_empty", "init_corrupt", "compared_method"}, default="init_corrupt")
    parser.add_argument("--compared_method", type=str, choices={"sr", "rog"}, default="sr")
    parser.add_argument("--dataset", type=str, help="choose the dataset. choices:\"cwq\", \"WebQSP\"", default='cwq')
    parser.add_argument("--llm", type=str, choices=LLM_BASE.keys(), default="gpt35", help="base LLM model.")
    parser.add_argument("--openai_api_keys", type=str, help="openai_api_keys", default="")
    
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args

def normalize(s: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    s = s.lower()
    exclude = set(string.punctuation)
    s = "".join(char for char in s if char not in exclude)
    s = re.sub(r"\b(a|an|the)\b", " ", s)
    # remove <pad> token:
    s = re.sub(r"\b(<pad>)\b", " ", s)
    s = " ".join(s.split())
    return s

def match(s1: str, s2: str) -> bool:
    s1 = normalize(s1)
    s2 = normalize(s2)
    return s2 in s1

def reasoning_path_analysis(input_file):
    """calculate some extensive features of reasoning path. 
    we experiment on 1000 examples of CWQ (we use 8 for maximum edit time, which can be modified according to current resources)

    Args:
        input_file: output of readi. Our current release does not cover the field "len_of_predict_knowledge" and "len_of_grounded_knowledge". We would release this version as soon as possible.
    """  
    refine_time = {i:0 for i in range(0,8)}
    if input_file.endswith("json"):
        data = readjson(input_file)
    elif input_file.endswith("jsonl"):
        data = read_jsonl(input_file)

    all_grounded = 0.0
    number_of_path = 0
    grounding_progress = 0.0
    len_of_predict_path = 0
    len_of_grounded_path = 0
    cvt_end = 0
    data = data[:1000]
    
    for lines in data:
        len_of_predict_knowledge, len_of_grounded_knowledge = lines['len_of_predict_knowledge'], lines['len_of_grounded_knowledge']
        number_of_path += len(len_of_predict_knowledge.keys())
        kg_paths = lines['kg_paths'].split("\n")
        for path in kg_paths:
            if path.split(" -> ")[-1].startswith("m."):
                cvt_end += 1
                break

        for k, v in len_of_predict_knowledge.items():
            grounding_progress += len_of_grounded_knowledge[k][-1] / v[-1]
            if len_of_grounded_knowledge[k][-1] == v[-1]:
                all_grounded += 1.0
                refine_time[len(len_of_grounded_knowledge[k])-1] += 1
                
            len_of_predict_path += v[-1]
            len_of_grounded_path += len_of_grounded_knowledge[k][-1]

    print("all grounded rate: ", all_grounded/number_of_path)
    print("avg grounded progress: ", grounding_progress/number_of_path)
    print("avg len of predict progress: ", len_of_predict_path/len(data))
    print("avg len of grounded progress: ", len_of_grounded_path/len(data))
    print("cvt ending rate: ", cvt_end/len(data))
    print("refine time grounded distribution: ", refine_time)


def calculate_answer_coverage_rate(file_path, golden_file_path):
    """calculate answer coverage rate of reasoning path. 
    we experiment on 1000 examples of CWQ (we use 8 for maximum edit time, which can be modified according to current resources)

    Args:
        file_path : _description_
        golden_file_path (_type_): _description_
    """
    if file_path.endswith("jsonl"):
        predict_graph = read_jsonl(file_path)[:1000]
    else:
        predict_graph = readjson(file_path)[:1000]

    golden = readjson(golden_file_path)
    all_recall = 0
    all_recall = 0
    all_knowledge_num = 0
    all_knowledge_one_path_num_questions = 0
    all_knowledge_one_path_num = 0
    recall_one_path = 0
    all_knowledge_multi_path_num_questions = 0
    all_knowledge_multi_path_num = 0
    recall_multi_path = 0

    for index, lines in enumerate(tqdm(predict_graph)):
        # topic entity (number of which is also the number of reasoning path)
        topic_entity = golden[index]['topic_entity']
        num_of_path = len(topic_entity.keys())
        lines['kg_triples'] = "\n".join(list(set(lines['kg_triples_str'].split("\n"))))
        answer_list = []

        if "cwq" in file_path:
            origin_data = golden[index]
            if 'answers' in origin_data:
                answers = origin_data["answers"]
            else:
                answers = origin_data["answer"]

            if type(answers) == str:
                answer_list.append(answers)
            else:
                alias = []
                for answer in answers:
                    if type(answer) == str:
                        alias.append(answer)
                    else:
                        alias = answer['label']
                    answer_list.extend(alias)
        

        knowledge_seq = lines['kg_triples'].replace(", ",",").replace(" ,",",").strip()
        rk = len(list(set(knowledge_seq.split("\n"))))
        all_knowledge_num += rk
        if num_of_path == 1:
            all_knowledge_one_path_num_questions += 1
            all_knowledge_one_path_num += rk
        else:
            all_knowledge_multi_path_num_questions += 1
            all_knowledge_multi_path_num += rk

        recall = 0
        for ans in answer_list:
            if match(knowledge_seq, ans):
                recall += 1

        all_recall += 1 if recall > 0 else 0
        if num_of_path == 1:
            recall_one_path += 1 if recall > 0 else 0
        else:
            recall_multi_path += 1 if recall > 0 else 0

    print("# knowledge one path:", all_knowledge_one_path_num_questions)
    print("# knowledge multi path:", all_knowledge_multi_path_num_questions)

    print("coverage rate overall:" , all_recall/len(predict_graph))

    print("coverage rate one path:" , recall_one_path/all_knowledge_one_path_num_questions)
    print("coverage rate multi path:" , recall_multi_path/all_knowledge_multi_path_num_questions)

    print("avg number of knowledge overall :" , all_knowledge_num/len(predict_graph))
    print("avg number of knowledge one path:" , all_knowledge_one_path_num/all_knowledge_one_path_num_questions)
    print("avg number of knowledge multi path:" , all_knowledge_multi_path_num/all_knowledge_multi_path_num_questions)


def analysis_for_different_reasoning_path():    
    options.LLM_type = LLM_BASE[options.llm]
        
    if options.analysis_strategy=="compared_method" and options.dataset != "cwq":
        print("compared methods must be cwq!")
        return 
    
    if options.analysis_strategy=="compared_method":
        input_file = os.path.join(OUTPUT_FILE_PATH, f"compare_model_path/cwq_{options.compared_method}_path.json")   
        output_file = os.path.join(OUTPUT_FILE_PATH, f"KGQA/{options.dataset}_{options.llm}_{options.analysis_strategy}_{options.compared_method}_{get_timestamp()}.jsonl")
        print("save output file to: ", output_file) 
        question_string = "question"
        dataset = question_process(input_file)
    else:
        question_string = get_question_string(options.dataset)
        input_file = get_dataset_file(options.dataset)
        dataset = question_process(input_file)
        output_file = os.path.join(OUTPUT_FILE_PATH, f"KGQA/{options.dataset}_{options.llm}_{options.analysis_strategy}_{get_timestamp()}.jsonl")
        print("save output file to: ", output_file)   
    
    if not options.full:
        dataset = dataset

    metrics = {
        'hit':[],
    }

    f = open(output_file, 'w+', encoding='utf-8')
    for index, item in enumerate(tqdm(dataset)):
        topic_ent_list = get_topic_entity_list(item, input_file)
        topic_ent_dict = get_topic_entity_dict(item, input_file)
        
        if topic_ent_list == []:
            print(f"{index} topic entity is empty, item: {item}")
            # this is critical. Please check if you need to continue
            continue
        
        question = item[question_string] if not item[question_string].endswith('?') else  item[question_string]+'?'
        ground_truth = get_ground_truth(item, options.dataset)
        init_reasoning_path = {}
        
        # reasoning path generation
        if options.analysis_strategy == "init_empty":
            init_reasoning_path = {
                    k: k
                    for k in topic_ent_list
                } 
            
        elif options.analysis_strategy == "init_corrupt":
            sample_relations = similar_relation_from_question(question, topk=10)
            for k in topic_ent_list:
                random_path_len = random.randint(0, 3) 
                randomed_relations = random.sample(sample_relations, random_path_len)
                init_reasoning_path[k] = k + " -> " + " -> ".join(randomed_relations)
                
        elif options.analysis_strategy == "compared_method":
            path_list = item['path_string_list']
            for line in path_list:
                entity = line.split(" -> ")[0].strip()
                if entity in topic_ent_list:
                        init_reasoning_path[entity] = line
        
        else:
            init_reasoning_path = get_init_reasoning_path(question, topic_ent_list, options)
        
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
                len_of_predict_knowledge[entity_label].append(len(init_reasoning_path[entity_label].split("->"))-1)
                len_of_grounded_knowledge[entity_label].append(max_path_len)    
                predict_path[entity_label].append(init_reasoning_path[entity_label])
                if options.verbose:
                    print("len of predict path", len(init_reasoning_path[entity_label].split("->"))-1)    

                if options.analysis_strategy != "init_only" and options.analysis_strategy != "compared_method" :
                    # invoke editing
                    if not end_refine:   
                        init_reasoning_path, thought = LLM_edit(init_reasoning_path, entity_label, feedback, question, options)
                        if options.verbose:
                            print(f"{f'feedback: {feedback}' if not end_refine else ''}")
                            print(f"Refine time:{refine}")
                            refine += 1
                
                # no more editing, post process of this path
                if end_refine or refine >= MAX_REFINE_TIME-1 or options.analysis_strategy == "init_only" or options.analysis_strategy == "compared_method":
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
                                        reasoning_paths=[grounded_path[1]]
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
        info = {
            'question':question,
            'init_path': init_reasoning_path,
            'predict': response,
            'ground_truth':ground_truth,
            'kg_instances': reasoning_paths,
            'thought': thought,
            'hit':hit,
        }
        d = json.dumps(info)
        f.write(d + '\n')

        metrics["hit"].append(hit)
        print(f"hit:{np.mean(metrics['hit'])}")

    f.close()
    print("\n" + "*" * 20 + "\n")
    print(f"hit:{np.mean(metrics['hit'])}")


if __name__ == '__main__':
    options = parse_args()
    analysis_for_different_reasoning_path()

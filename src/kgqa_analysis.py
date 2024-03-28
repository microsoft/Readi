import sys
import os
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

def main_analysis():    
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
    main_analysis()

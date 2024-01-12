import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
import utils
import argparse
from tqdm import tqdm
from llms.language_models import get_registed_model
import os
from datasets import load_dataset
from eval.evaluate_results import eval_result
import json
from multiprocessing import Pool
from build_qa_input import PromptBuilder
from functools import partial
from config import *
from utils.utils import get_timestamp

def get_output_file(path, force=False):
    if not os.path.exists(path) or force:
        fout = open(path, "w")
        return fout, []
    else:
        with open(path, "r") as f:
            processed_results = []
            for line in f:
                try:
                    results = json.loads(line)
                except:
                    raise ValueError("Error in line: ", line)
                processed_results.append(results["id"])
        fout = open(path, "a")
        return fout, processed_results

def prediction_graph(data, processed_list, input_builder, reasoning_path_LLM):
    question = data["question"]
    answer = data["answer"]
    id = data["id"]
    if id in processed_list:
        return None


    kg_triples, kg_paths = input_builder.get_graph_knowledge_LLM_revised(data, reasoning_path_LLM['relation_path_candidates'])

    process_ed_kg = ""
    kg_triple_set = []
    for lines in kg_triples:
        for l in lines:
            triple = [l[0] , l[1] , l[2]]
            if triple not in kg_triple_set:
                kg_triple_set.append(triple)

    for l in kg_triple_set:
        process_ed_kg += "(" + l[0] + ", " + l[1] + ", " + l[2] + " )\n"

    process_ed_kg = process_ed_kg.strip("\n")

    if kg_paths is None:
        return None

    result = {
        "id": id,
        "question": question,
        "kg_triples_str": process_ed_kg,
        "kg_triples_set": kg_triple_set,
        "kg_paths": "\n".join(kg_paths),
        "ground_truth": answer,
        "input": question,
    }
    return result

# 前处理 后处理 存文件
def prediction_graph_engine(args, processed_list, input_builder, data):
    question = data[get_question_string(args.dataset)]
    answer = get_entity_answer(data, args.dataset)
    id = data[get_question_id(args.dataset)]
    thought = ""
    if id in processed_list:
        return None

    if args.refine_strategy=="llm_refine":
        kg_triples, kg_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path = input_builder.get_graph_knowledge_LLM_revised_engine(args, data)
    # 只要init plan
    elif args.refine_strategy=="init_only":
        kg_triples, kg_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path = input_builder.get_graph_knowledge_LLM_init_plan(args, data)

    # init plan为空
    elif args.refine_strategy =="init_empty":
        kg_triples, kg_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path = input_builder.get_graph_knowledge_LLM_empty_init(args, data)

    process_ed_kg = ""
    kg_triple_set = []
    for lines in kg_triples:
        for l in lines:
            triple = [l[0] , l[1] , l[2]]
            if triple not in kg_triple_set:
                kg_triple_set.append(triple)

    for l in kg_triple_set:
        process_ed_kg += "(" + l[0] + ", " + l[1] + ", " + l[2] + " )\n"

    process_ed_kg = process_ed_kg.strip("\n")

    if kg_paths is None:
        return None

    result = {
        "id": id,
        "question": question,
        "kg_triples_str": process_ed_kg,
        "kg_triples_set": kg_triple_set,
        "kg_paths": "\n".join(kg_paths),
        "len_of_predict_knowledge": len_of_predict_knowledge,
        "len_of_grounded_knowledge": len_of_grounded_knowledge,
        "predict_path": predict_path,
        "ground_truth": answer,
        "LLM-thoughts":thought,
        "input": question,
    }
    return result


def main_engine(args, LLM):
    rule_postfix = "no_rule"
    # Load dataset
    if args.add_rule:
        rule_postfix = args.rule_path.replace("/", "_").replace(".", "_")
        if args.use_true:
            rule_postfix = "ground_rule"
        elif args.use_random:
            rule_postfix = "random_rule"

    if args.cot:
        rule_postfix += "_cot"
    if args.explain:
        rule_postfix += "_explain"
    if args.filter_empty:
        rule_postfix += "_filter_empty"
    if args.each_line:
        rule_postfix += "_each_line"

    print("Load dataset from finished")
    output_dir = os.path.join(
        # args.predict_path, args.d, args.model_name, args.split, rule_postfix
        args.predict_path, args.dataset
    )
    print("Save results to: ", output_dir)
    # Predict
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    model = LLM(args)
    input_builder = PromptBuilder(
        # args.prompt_path,
        args.add_rule,
        use_true=args.use_true,
        cot=args.cot,
        explain=args.explain,
        use_random=args.use_random,
        each_line=args.each_line,
        maximun_token=model.maximun_token,
        tokenize=model.tokenize,
    )
    print("Prepare pipline for inference...")

    # Save args file
    with open(os.path.join(output_dir, "args.txt"), "w") as f:
        json.dump(args.__dict__, f, indent=2)

    output_file = os.path.join(output_dir, args.output_file_name)
    fout, processed_list = get_output_file(output_file, force=args.force)

    with open(args.init_plan_path, 'r') as f:
        reasoning_path = json.load(f)

    for index, data in enumerate(tqdm(reasoning_path)):
        res = prediction_graph_engine(args, processed_list, input_builder, data)
        if res is not None:
            if args.debug:
                print(json.dumps(res))
            fout.write(json.dumps(res) + "\n")
            fout.flush()
    fout.close()

    # eval_result(output_file)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument( "--data_path", type=str, default="rmanluo")
    argparser.add_argument("--dataset","-d", type=str, default=None, help="dataset alias or prefix")
    argparser.add_argument("--split", type=str, default="test")
    argparser.add_argument("--predict_path", type=str, default="results/KGQA")
    argparser.add_argument(
        "--model_name",
        type=str,
        help="model_name for save results",
        default="RoG",
    )
    argparser.add_argument(
        "--prompt_path",
        type=str,
        help="prompt_path",
        default="../reasoning-on-graphs/prompts/llama2_predict.txt",
    )
    argparser.add_argument("--add_rule", default=True ,action="store_true")
    argparser.add_argument("--use_true", action="store_true")
    argparser.add_argument("--cot", action="store_true")
    argparser.add_argument("--explain", action="store_true")
    argparser.add_argument("--use_random", action="store_true")
    argparser.add_argument("--each_line", action="store_true")
    argparser.add_argument(
        "--rule_path",
        type=str,
        default="reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_3_False.jsonl",
    )
    argparser.add_argument( "--force", "-f", action="store_true", help="force to overwrite the results")
    argparser.add_argument("-n", default=1, type=int, help="number of processes")
    argparser.add_argument("--filter_empty", action="store_true")
    argparser.add_argument("--debug", action="store_true")
    argparser.add_argument("--temperature_refine", type=float, default=0.3, help="llm temperature refine ")

    argparser.add_argument("--refine_strategy", type=str, choices={"llm_refine", "init_only", "init_empty"}, default="init_empty")
    argparser.add_argument("--refine_output", type=str, choices={"sequence", "function", "dict", "sequence_err_msg", "function_err_msg"}, default="sequence_err_msg")
    argparser.add_argument("--llm", type=str, choices=LLM_BASE.keys(), default='gpt35')
    argparser.add_argument("--init_plan_path", type=str, required=True, default=None)
    # argparser.add_argument("--output_file_name", type=str, default="predictions_kg_with_input_llm_cwq100_path_onePath_gpt4_1230_engine_triple_cvt_new_goal_progess_hard_stop.jsonl")
    argparser.add_argument("--name", type=str, default="onePath_CVT_HardStop_oldengine_thought")

    args, _ = argparser.parse_known_args()
    if args.dataset is None:
        args.dataset = os.path.split(args.init_plan_path)[1].split('_')[0]

    args.output_file_name = f"{args.dataset}_{args.llm}_{args.refine_strategy}_{args.refine_output}_{args.name}_{get_timestamp()}.jsonl"
    print(args.output_file_name)

    args.llm_engine = LLM_BASE[args.llm]

    if args.model_name != "no-llm":
        LLM = get_registed_model(args.model_name)
        LLM.add_args(argparser)
    else:
        LLM = None
    # args = argparser.parse_args()

    main_engine(args, LLM)

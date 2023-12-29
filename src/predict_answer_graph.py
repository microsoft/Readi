import sys
import os

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
import utils
import argparse
from tqdm import tqdm
from llms.language_models import get_registed_model
import os
from datasets import load_dataset
from evaluate_results import eval_result
import json
from multiprocessing import Pool
from build_qa_input import PromptBuilder
from functools import partial

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


def merge_rule_result(qa_dataset, rule_dataset, n_proc=1, filter_empty=False):
    question_to_rule = dict()
    for data in rule_dataset:
        qid = data["id"]
        predicted_paths = data["prediction"]
        ground_paths = data["ground_paths"]
        question_to_rule[qid] = {
            "predicted_paths": predicted_paths,
            "ground_paths": ground_paths,
        }

    def find_rule(sample):
        qid = sample["id"]
        sample["predicted_paths"] = []
        sample["ground_paths"] = []
        sample["predicted_paths"] = question_to_rule[qid]["predicted_paths"]
        sample["ground_paths"] = question_to_rule[qid]["ground_paths"]
        return sample  # TODO: ignore the sample with zero paths.

    qa_dataset = qa_dataset.map(find_rule, num_proc=n_proc)
    if filter_empty:
        qa_dataset = qa_dataset.filter(
            lambda x: len(x["ground_paths"]) > 0, num_proc=n_proc
        )
    return qa_dataset


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
def prediction_graph_engine(processed_list, input_builder, reasoning_path_LLM, llm_engine):
    question = reasoning_path_LLM["question"]
    answer = reasoning_path_LLM["answer"]
    id = reasoning_path_LLM["ID"]
    thought = ""
    if id in processed_list:
        return None

    kg_triples, kg_paths, thought = input_builder.get_graph_knowledge_LLM_revised_engine(reasoning_path_LLM, llm_engine)

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
        "LLM-thoughts":thought,
        "input": question,
    }
    return result



def prediction(data, processed_list, input_builder, model):
    question = data["question"]
    answer = data["answer"]
    id = data["id"]
    if id in processed_list:
        return None
    if model is None:
        prediction = input_builder.direct_answer(data)
        return {
            "id": id,
            "question": question,
            "prediction": prediction,
            "ground_truth": answer,
            "input": question,
        }
    input = input_builder.process_input(data)
    prediction = model.generate_sentence(input)
    if prediction is None:
        return None
    result = {
        "id": id,
        "question": question,
        "prediction": prediction,
        "ground_truth": answer,
        "input": input,
    }
    return result


def main(args, LLM):
    input_file = os.path.join(args.data_path, args.d)
    rule_postfix = "no_rule"
    # Load dataset
    dataset = load_dataset(input_file, split=args.split)
    if args.add_rule:
        rule_postfix = args.rule_path.replace("/", "_").replace(".", "_")
        rule_dataset = utils.load_jsonl(args.rule_path)
        dataset = merge_rule_result(dataset, rule_dataset, args.n, args.filter_empty)
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
        args.predict_path, args.d, args.model_name, args.split, rule_postfix
    )
    print("Save results to: ", output_dir)
    # Predict
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    if LLM is not None:
        model = LLM(args)
        input_builder = PromptBuilder(
            args.prompt_path,
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
        # model.prepare_for_inference()
    else:
        model = None
        # Directly return last entity as answer
        input_builder = PromptBuilder(
            args.prompt_path, args.add_rule, use_true=args.use_true
        )

    # Save args file
    with open(os.path.join(output_dir, "args.txt"), "w") as f:
        json.dump(args.__dict__, f, indent=2)

    output_file = os.path.join(output_dir, f"predictions_kg_with_input_llm_cwq100_path_onePath_gpt4_1227_llm_stop.jsonl")
    fout, processed_list = get_output_file(output_file, force=args.force)

    if args.n > 1:
        with Pool(args.n) as p:
            for res in tqdm(
                p.imap(
                    partial(
                        prediction,
                        processed_list=processed_list,
                        input_builder=input_builder,
                        model=model,
                    ),
                    dataset,
                ),
                total=len(dataset),
            ):
                if res is not None:
                    if args.debug:
                        print(json.dumps(res))
                    fout.write(json.dumps(res) + "\n")
                    fout.flush()
    else:
        # for index, data in enumerate(tqdm(dataset)):
        #     # res = prediction(data, processed_list, input_builder, model)
        #     res = prediction_graph_engine(data, processed_list, input_builder, reasoning_path[index])
        #     if res is not None:
        #         if args.debug:
        #             print(json.dumps(res))
        #         fout.write(json.dumps(res) + "\n")
        #         fout.flush()
        # fout.close()    
           
        with open(args.init_plan_path, 'r') as f:
            reasoning_path = json.load(f)

        for index, data in enumerate(tqdm(dataset)):
            # res = prediction(data, processed_list, input_builder, model)
            res = prediction_graph_engine(data, processed_list, input_builder, reasoning_path[index])
            if res is not None:
                if args.debug:
                    print(json.dumps(res))
                fout.write(json.dumps(res) + "\n")
                fout.flush()
    fout.close()

    # eval_result(output_file)



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
        args.predict_path, args.d, args.model_name, args.split, rule_postfix
    )
    print("Save results to: ", output_dir)
    # Predict
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    model = LLM(args)
    input_builder = PromptBuilder(
        args.prompt_path,
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
        res = prediction_graph_engine(processed_list, input_builder, data, args.llm_engine)
        if res is not None:
            if args.debug:
                print(json.dumps(res))
            fout.write(json.dumps(res) + "\n")
            fout.flush()
    fout.close()

    # eval_result(output_file)


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "--data_path", type=str, default="rmanluo"
    )
    argparser.add_argument("--d", "-d", type=str, default="RoG-cwq")
    argparser.add_argument("--split", type=str, default="test")
    argparser.add_argument("--predict_path", type=str, default="/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA")
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
        default="/home/v-sitaocheng/demos/llm_hallu/reasoning-on-graphs/prompts/llama2_predict.txt",
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
        default="/home/v-sitaocheng/demos/llm_hallu/reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_3_False.jsonl",
    )
    argparser.add_argument(
        "--force", "-f", action="store_true", help="force to overwrite the results"
    )
    argparser.add_argument("-n", default=1, type=int, help="number of processes")
    argparser.add_argument("--filter_empty", action="store_true")
    argparser.add_argument("--debug", action="store_true")
    # argparser.add_argument("--llm_engine", type=str, default="gpt-4-32k-20230321")
    argparser.add_argument("--llm_engine", type=str, default="gpt-35-turbo-16k-20230613")
    argparser.add_argument("--init_plan_path", type=str, default="/home/v-sitaocheng/demos/dangle_over_ground/data/initial_plan/cwq_test_1221.json")
    argparser.add_argument("--output_file_name", type=str, default="predictions_kg_with_input_llm_cwq100_path_onePath_gpt35_1229_agent.jsonl")
        
    args, _ = argparser.parse_known_args()
    if args.model_name != "no-llm":
        LLM = get_registed_model(args.model_name)
        LLM.add_args(argparser)
    else:
        LLM = None
    args = argparser.parse_args()

    main_engine(args, LLM)

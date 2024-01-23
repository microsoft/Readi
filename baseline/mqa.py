import json
import numpy as np
from tqdm import tqdm
from argparse import ArgumentParser
from collections import defaultdict
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from src.config import LLM_BASE
from utils.utils import run_llm, get_timestamp


DATA_PATH = "data/datasets/metaQA"
PROMPT_PATH = "prompt/metaQA"


def question_process(fpath: str):
    qa_pairs = []
    with open(fpath, 'r', encoding='utf-8') as f:
        data = f.readlines()
        data = [d.strip('\n') for d in data]
    for qa in data:
        q, a = qa.split('\t')
        answer_list = a.split('|')
        entity = q[q.index('[') + 1: q.index(']')]
        qa_dict = {
            'question': q,
            'entity': entity,
            'answer': answer_list
        }
        qa_pairs.append(qa_dict)
    return qa_pairs


def parse_args():
    parser = ArgumentParser("KBQA MQA dataset")
    parser.add_argument("--hop", type=str,
                        choices=['1hop', '2hop', '3hop'], default='2hop')
    parser.add_argument("--full", action="store_true", help="full dataset.")
    parser.add_argument("--verbose", action="store_true", help="verbose.")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=4096)
    parser.add_argument("--llm", type=str, choices=LLM_BASE.keys(),
                        default="gpt35", help="base LLM model.")
    parser.add_argument("--prompt_retrieve",
                        action="store_true", help="use prompt to retrieve.")
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args


def call_llm(prompt):
    MAX_RETRY_TIME = 5
    for _ in range(MAX_RETRY_TIME):
        try:
            response = run_llm(
                prompt,
                options.temperature,
                options.max_token,
                options.LLM_type
            )
            if 'sorry' in response:
                return ""
            results = eval(response)
            return results
        except Exception as e:
            results = ""
            continue
    return results


def get_direct_io(question):
    prompt = open(
        os.path.join(PROMPT_PATH, f"direct_3hop.md"),
        'r', encoding='utf-8'
    ).read()
    prompt += f"\nQ: {question}\nA:"
    result = call_llm(prompt)
    result = [str(r) for r in result]
    return result


def main():
    dataset = question_process(os.path.join(
        DATA_PATH,
        f'qa_test_{options.hop}.txt'
    ))

    if not options.full:
        dataset = dataset[:100]

    metrics = {
        'hit': [],
        'coverage': []
    }
    f = open(
        f"results/MQA/MetaQA_{options.hop}_{get_timestamp()}.jsonl", 'w+', encoding='utf-8')
    for question_dict in tqdm(dataset):
        question = question_dict['question'].replace("\[", '').replace('\]', '')
        ground_truth = question_dict['answer']
        result = get_direct_io(question)
        if options.verbose:
            print(f"Question: {question}, Answer: {result}")
        hit, coverage = evaluate(result, ground_truth)
        info = {
            'question': question,
            'answer_list': result,
            'hit': hit,
            'coverage': coverage
        }
        d = json.dumps(info, ensure_ascii=False)
        f.write(d + '\n')

        metrics['hit'].append(hit)
        metrics['coverage'].append(coverage)
        print(f"hit: {np.mean(metrics['hit'])}")
        print(f"coverage: {np.mean(metrics['coverage'])}")

    f.close()
    print("\n" + "*" * 20 + "\n")
    print(f"hit: {np.mean(metrics['hit'])}")
    print(f"coverage: {np.mean(metrics['coverage'])}")


def evaluate(answer_list, ground_truth):
    """return hit, coverage"""
    answers = set([ans.lower() for ans in answer_list])
    ground_truths = set([ans.lower() for ans in ground_truth])
    intersect = answers.intersection(ground_truths)
    coverage = len(intersect) / len(ground_truths)
    hit = 1 if len(intersect) > 0 else 0
    return hit, coverage


if __name__ == '__main__':
    options = parse_args()
    main()

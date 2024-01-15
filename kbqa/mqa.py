import sys
import os
from collections import defaultdict
from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np

sys.path.append(os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "/.."
))

from config import *
from utils.utils import run_llm

DATA_PATH = "data/datasets/metaQA"
TYPE_RELATION = {
    "tag_to_movie": "has_tags",
    "writer_to_movie": "written_by",
    "movie_to_tags": "has_tags",
    "movie_to_year": "release_year",
    "movie_to_writer": "written_by",
    "movie_to_language": "in_language",
    "movie_to_genre": "has_genre",
    "director_to_movie": "directed_by",
    "movie_to_actor": "starred_actors",
    "movie_to_director": "directed_by",
    "actor_to_movie": "starred_actors"
}
MAX_REFINE_TIME = 5

PROMPT = """You are a reasoning chain planner.
Given the following operations: actor_to_movie, movie_to_writer, tag_to_movie, writer_to_movie, movie_to_year, director_to_movie, movie_to_language, movie_to_genre, movie_to_director, movie_to_actor, movie_to_tags."""

EXAMPLES = """EXAMPLES:"""

def parse_args():
    parser = ArgumentParser("KBQA MQA dataset")
    parser.add_argument(
        "--hop",
        type=str,
        choices=['1hop', '2hop', '3hop'],
        default='1hop'
    )
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=4096)
    parser.add_argument(
        "--llm",
        type=str,
        choices=LLM_BASE.keys(),
        default="gpt35",
        help="base LLM model."
    )
    parser.add_argument(
        "--prompt_retrieve",
        action="store_true",
        help="use prompt to retrieve."
    )
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args



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


class MetaKG():
    def __init__(self, kg_path: str) -> None:
        self.relation_dict = defaultdict(defaultdict(list))
        with open(kg_path, 'r', encoding='utf-8') as f:
            data = f.readlines()
            data = [d.strip('\n') for d in data]
        for fact in data:
            s, r, t = fact.split('|')
            self.relation_dict[s][r].append(t)

    def get_cand_relations(self, s):
        return self.relation_dict[s].keys()

    def get_cand_entities(self, s, r):
        return self.relation_dict[s][r]

def retrieve_few_shot(question, entity):
    raise NotImplementedError()
    return """Question: XXX
    Reasoning Path: XXX"""

def get_init_reasoning(question, entity):
    prompt = PROMPT
    if options.prompt_retrieve:
        prompt += retrieve_few_shot(question, entity)
    else:
        prompt += EXAMPLES

    prompt += f"""Question: {question}
    Answer: """

    MAX_RETRY_TIME = 5
    for _ in range(MAX_RETRY_TIME):
        try:
            response = run_llm(
                prompt,
                options.temperature,
                options.max_token,
                options.LLM_type
            )
            result = eval(response.split("Answer:")[-1].strip())
            break
        except Exception as e:
            continue
    return result
    # return ['actor_to_movie', 'movie_to_writter']

def parse_answer(answer, entity, kg):
    raise NotImplementedError()
    return ['writer1', 'writer2']

def refine_reasoning(question, entity, answer, error_info):
    raise NotImplementedError()
    return ['actor_to_movie', 'movie_to_writter']

def evaluate(answer_list, ground_truth):
    """return hit, coverage"""
    raise NotImplementedError()
    return 1, 0.7


def main():
    kg = MetaKG(os.path.join(DATA_PATH, 'kb.txt'))
    dataset = question_process(os.path.join(
        DATA_PATH,
        'qa_test_{options.hop}.txt'
    ))

    metrics = {
        'hit': [],
        'coverage': []
    }
    for question_dict in tqdm(dataset):
        question = question_dict['question']
        entity = question_dict['entity']
        ground_truth = question_dict['answer']

        answer = get_init_reasoning(question, entity)
        refine = 0
        while refine < MAX_REFINE_TIME:
            answer_list, feedback = parse_answer(answer, entity, kg)
            if not feedback:
                break
            answer = refine_reasoning(question, entity, answer, feedback)

        hit, coverage = evaluate(answer_list, ground_truth)
        metrics["hit"].append(hit)
        metrics["coverage"].append(coverage)

    print(f"hit: {np.mean(metrics['hit'])}")
    print(f"coverage: {np.mean(metrics['coverage'])}")





if __name__ == '__main__':
    options = parse_args()
    main(options)

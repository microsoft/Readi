import sys
import os
from collections import defaultdict
from argparse import ArgumentParser
from tqdm import tqdm
import numpy as np
from config import LLM_BASE, MAX_LLM_RETRY_TIME, MAX_REFINE_TIME
import json

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.utils import run_llm, get_timestamp

DATA_PATH = "data/datasets/metaQA"
PROMPT_PATH = "prompt/metaQA"
TYPE_RELATION = {
    "tag_to_movie": "tagged",
    "writer_to_movie": "write",
    "movie_to_tags": "has_tags",
    "movie_to_year": "release_year",
    "movie_to_writer": "written_by",
    "movie_to_language": "in_language",
    "movie_to_genre": "has_genre",
    "director_to_movie": "direct",
    "movie_to_actor": "starred_actors",
    "movie_to_director": "directed_by",
    "actor_to_movie": "starred"
}

REVERSE_TYPE_MAPPING = {
    TYPE_RELATION["tag_to_movie"]: TYPE_RELATION["movie_to_tags"],
    TYPE_RELATION["movie_to_tags"]: TYPE_RELATION["tag_to_movie"],
    TYPE_RELATION["writer_to_movie"]: TYPE_RELATION["movie_to_writer"],
    TYPE_RELATION["movie_to_writer"]: TYPE_RELATION["writer_to_movie"],
    TYPE_RELATION["director_to_movie"]: TYPE_RELATION["movie_to_director"],
    TYPE_RELATION["movie_to_director"]: TYPE_RELATION["director_to_movie"],
    TYPE_RELATION["actor_to_movie"]: TYPE_RELATION["movie_to_actor"],
    TYPE_RELATION["movie_to_actor"]: TYPE_RELATION["actor_to_movie"]
}

def parse_args():
    parser = ArgumentParser("KBQA MQA dataset")
    parser.add_argument("--hop", type=str, choices=['1hop', '2hop', '3hop'], default='2hop')
    parser.add_argument("--full", action="store_true", help="full dataset.", default=True)
    parser.add_argument("--verbose", action="store_true", help="verbose.")
    parser.add_argument("--temperature", type=float, default=0.3)
    parser.add_argument("--max_token", type=int, default=2048)
    parser.add_argument("--llm", type=str, choices=LLM_BASE.keys(), default="gpt35", help="base LLM model.")
    parser.add_argument("--openai_api_keys", help="openai_api_keys")
    args = parser.parse_args()
    args.LLM_type = LLM_BASE[args.llm]
    return args


def question_process(fpath: str):
    """preprocess data items

    Args:
        fpath

    Returns:
        data item dict
    """
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
    """
        KG loading and other utils
    """
    def __init__(self, kg_path: str) -> None:
        self.relation_dict = defaultdict(lambda: defaultdict(list))
        with open(kg_path, 'r', encoding='utf-8') as f:
            data = f.readlines()
            data = [d.strip('\n') for d in data]
        for fact in tqdm(data, desc="Building MetaKG"):
            s, r, t = fact.split('|')
            self.relation_dict[s][r].append(t)

            if r in REVERSE_TYPE_MAPPING.keys():
                reversed_r = REVERSE_TYPE_MAPPING[r]
                self.relation_dict[t][reversed_r].append(s)
        print(f"MetaKG size: {len(self.relation_dict)}")

    def get_cand_relations(self, s):
        if s not in self.relation_dict.keys():
            return []
        return self.relation_dict[s].keys()

    def get_cand_entities(self, s, r):
        if s not in self.relation_dict.keys():
            return []
        return self.relation_dict[s].get(r, [])


def get_init_reasoning(question, entity):
    """generate initial reasoning path

    Args:
        question : the given question
        entity : topic entity

    Returns:
        result: reasoning path
    """
    prompt = open(
        os.path.join(PROMPT_PATH, f"init_{options.hop}.md"),
        'r', encoding='utf-8'
    ).read()
    prompt += f"\nQuestion: {question}\n"
    if options.hop != '1hop':
        prompt += "<Thought>\n"
    result = call_llm(prompt)
    return result

def parse_answer(answer, entity, kg: MetaKG):
    """KG instantiation. Detect feedback if anything goes wrong. If not, provide instantiation results

    Args:
        answer : predicted reasoning path
        entity : topic entity
        KG (MetaKG)

    Returns:
        entries: the instantiation results. For MQA, this is the answer of question
        feedback: feedback if anything goes wrong
    """
    hop = {'1hop': 1, '2hop': 2, '3hop': 3}[options.hop]
    if len(answer) != hop:
        return [], f"There should be {hop} relations, but got {len(answer)}."

    feedback = ""
    entries = [entity]

    reasoning = [f"[{entity}]"]
    for iter, relation in enumerate(answer):
        cand_entries = []
        reasoning = [f"{r} -> {relation}" for r in reasoning]
        new_reasoning = []
        for entry, reason_path in zip(entries, reasoning):
            # Relation not in candidate
            if relation not in TYPE_RELATION.keys():
                feedback += f"Relation {relation} not in candidate relations. You can only choose from ['actor_to_movie', 'movie_to_writer', 'tag_to_movie', 'writer_to_movie', 'movie_to_year', 'director_to_movie', 'movie_to_language', 'movie_to_genre', 'movie_to_director', 'movie_to_actor', 'movie_to_tags']."
                continue
            transformed_relation = TYPE_RELATION[relation]
            # transformed_relation = TYPE_RELATION.get(relation, relation)
            if transformed_relation not in kg.get_cand_relations(entry):
                # select wrong relation from candidate [entry]
                feedback += f"Previous reasoning path: {reason_path}\n"
                feedback += f"Relation {relation} not in candidate relations of entity [{entry}].\n"
                cand_relation = [
                    k for k in TYPE_RELATION.keys()
                    if TYPE_RELATION[k] in kg.get_cand_relations(entry)
                ]
                feedback += f"You can only choose from: {cand_relation}\n"
                continue
            cand_entry = kg.get_cand_entities(entry, transformed_relation)
            cand_entries.extend(cand_entry)
            new_reasoning.extend([f"{reason_path} -> [{cand}]" for cand in cand_entry])
        entries = cand_entries
        reasoning = new_reasoning
    return entries, feedback

def call_llm(prompt):
    """call llm for reasoning path generation or editing

    Args:
        prompt

    Returns:
        reasoning path: chosen headers and entities
    """
    for _ in range(MAX_LLM_RETRY_TIME):
        try:
            response = run_llm(prompt, options.temperature, options.max_token, options.openai_api_keys, options.LLM_type)
            relations = response.split("Relations: ")[-1].strip('\n').strip()
            results = eval(relations)
            assert type(results) == list
            break
        except Exception as e:
            results = []
            continue
    return results


def refine_reasoning(question, entity, answer, feedback):
    """editing reasoning path

    Args:
        question : the given question
        entity : topic entities
        answer : previous reasoning path
        feedback : feedback from instantiation

    Returns:
        answer: edited reasoning path
    """
    prompt = open(
        os.path.join(PROMPT_PATH, f"refine_{options.hop}.md"),
        'r', encoding='utf-8'
    ).read()
    append = f"""\nQuestion: {question}\nWrong Answer: {answer}\n<Feedback>\n{feedback}\n</Feedback>\n<Thought>\n"""
    prompt += append
    print(f"Question: {question}, Feedback: {feedback}")
    answer = call_llm(prompt)
    print(f"refine answer: {answer}")
    return answer


def evaluate(answer_list, ground_truth):
    """return hit, coverage"""
    answers = set([ans.lower() for ans in answer_list])
    ground_truths = set([ans.lower() for ans in ground_truth])
    intersect = answers.intersection(ground_truths)
    coverage = len(intersect) / len(ground_truths)
    hit = 1 if len(intersect) > 0 else 0
    return hit, coverage


def main():
    kg = MetaKG(os.path.join(DATA_PATH, 'kb.txt'))
    dataset = question_process(os.path.join(
        DATA_PATH,
        f'qa_test_{options.hop}.txt'
    ))

    if not options.full:
        dataset = dataset[:1000]

    metrics = {
        'hit': [],
        'coverage': []
    }

    f = open(f"results/MQA/MetaQA_{options.hop}_{get_timestamp()}.jsonl", 'w+', encoding='utf-8')
    for question_dict in tqdm(dataset):
        question = question_dict['question']
        entity = question_dict['entity']
        ground_truth = question_dict['answer']

        # reasoning path generation
        answer = get_init_reasoning(question, entity)
        if options.verbose:
            print(f"Question: {question}")
            print(f"Reasoning Path: {answer}")
        refine = 0

        answers = []
        feedbacks = []
        while refine < MAX_REFINE_TIME:
            # reasoning path instantiation. collect feedback if anything goes wrong.
            answer_list, feedback = parse_answer(answer, entity, kg)
            answers.append(answer_list)
            feedbacks.append(feedback)
            if answer_list:
                break
            if options.verbose:
                print(f"{answer_list}, {f'feedback: {feedback}' if feedback else ''}")
                print(f"Refine: {refine}")
            # reasoning path editing (no need to reasoning the answer for MQA)
            answer = refine_reasoning(question, entity, answer, feedback)
            refine += 1

        hit, coverage = evaluate(answer_list, ground_truth)
        info = {
            'question': question,
            'answer': answer_list,
            'history': answers,
            'feedback': feedbacks,
            'hit': hit,
            'coverage': coverage,
        }
        d = json.dumps(info)
        f.write(d + '\n')

        metrics["hit"].append(hit)
        metrics["coverage"].append(coverage)
        print(f"hit: {np.mean(metrics['hit'])}")
        print(f"coverage: {np.mean(metrics['coverage'])}")

    f.close()
    print("\n" + "*" * 20 + "\n")
    print(f"hit: {np.mean(metrics['hit'])}")
    print(f"coverage: {np.mean(metrics['coverage'])}")

if __name__ == '__main__':
    options = parse_args()
    main()

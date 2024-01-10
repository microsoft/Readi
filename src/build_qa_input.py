import sys
import os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
import utils
import random
from typing import Callable
import numpy as np
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
import json
import time
import openai
from utils.cloudgpt_aoai_new import *
from utils.prompt_list import *
from config import *
import time



class PromptBuilder(object):
    MCQ_INSTRUCTION = """Please answer the following questions. Please select the answers from the given choices and return the answer only."""
    SAQ_INSTRUCTION = """Please answer the following questions. Please keep the answer as simple as possible and return all the possible answer as a list."""
    MCQ_RULE_INSTRUCTION = """Based on the reasoning paths, please answer the given question. Please select the answers from the given choices and return the answers only."""
    SAQ_RULE_INSTRUCTION = """Based on the reasoning paths, please answer the given question. Please keep the answer as simple as possible and return all the possible answers as a list."""
    COT = """ Let's think it step by step."""
    EXPLAIN = """ Please explain your answer."""
    QUESTION = """Question:\n{question}"""
    GRAPH_CONTEXT = """Reasoning Paths:\n{context}\n\n"""
    CHOICES = """\nChoices:\n{choices}"""
    EACH_LINE = """ Please return each answer in a new line."""

    # def __init__(self, prompt_path, add_rule = True, use_true = False, cot = False, explain = False, use_random = False, each_line = False, maximun_token = 4096, tokenize: Callable = lambda x: len(x)):
    def __init__(self,  add_rule = True, use_true = False, cot = False, explain = False, use_random = False, each_line = False, maximun_token = 4096, tokenize: Callable = lambda x: len(x)):
        # self.prompt_template = self._read_prompt_template(prompt_path)
        self.add_rule = add_rule
        self.use_true = use_true
        self.use_random = use_random
        self.cot = cot
        self.explain = explain
        self.maximun_token = maximun_token
        self.tokenize = tokenize
        self.each_line = each_line

        query_encoder = AutoQueryEncoder(encoder_dir='facebook/contriever', pooling='mean')
        self.corpus = LuceneSearcher(os.path.join(KB_BINDER_PATH, "contriever_fb_relation/index_relation_fb"))
        bm25_searcher = LuceneSearcher(os.path.join(KB_BINDER_PATH, 'contriever_fb_relation/index_relation_fb'))
        contriever_searcher = FaissSearcher(os.path.join(KB_BINDER_PATH, 'contriever_fb_relation/freebase_contriever_index'), query_encoder)

        self.hsearcher = HybridSearcher(contriever_searcher, bm25_searcher)

    def _read_prompt_template(self, template_file):
        with open(template_file) as fin:
            prompt_template = f"""{fin.read()}"""
        return prompt_template

    def apply_rules(self, graph, rules, srouce_entities):
        results = []
        for entity in srouce_entities:
            for rule in rules:
                res = utils.bfs_with_rule(graph, entity, rule)
                results.extend(res)
        return results

    def apply_rules_LLM(self, graph, rules, srouce_entities, grounded_relations):
        results = []
        for entity in srouce_entities:
            for rule in rules:
                reasoning_set = []
                for relation in rule:
                    reasoning_set.append(grounded_relations[relation])
                res = utils.bfs_with_rule_LLM(graph, entity, rule, reasoning_set)
                results.extend(res)

        return results



    def apply_rules_LLM_revised(self, graph, rules, srouce_entities, grounded_relations):
        results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True
        one_path = True
        if path is True:
            new_rules = {}
            for k, v in rules.items():
                if type(v)==list:
                    new_rules[k] = utils.string_to_path(v[0])
                else:
                    new_rules[k] = utils.string_to_path(v)
            rules = new_rules

        for entity in srouce_entities:

            # for rule in rules[entity]:
            #   grounded relations for each relation in rules
            if entity not in rules.keys():
                continue

            # 注意,每次得到的grounded knowledge和result只会和一个topic entity有关!!!!
            grounded_reasoning_set = []
            if type(rules[entity][0])==str:
                for relation in rules[entity]:
                    grounded_reasoning_set.append(grounded_relations[relation])
            else:
                for relation in rules[entity][0]:
                    grounded_reasoning_set.append(grounded_relations[relation])

            if type(rules[entity][0])==str:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM(graph, entity, rules[entity], grounded_reasoning_set)
            else:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM(graph, entity, rules[entity][0], grounded_reasoning_set)


            # 当前实体出发  如果非空,说明grounding成功, 加入路径
            if len(result_paths) > 0:
                results.extend(result_paths)

            # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
            else:
                return results, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict



        return results, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict



    def apply_rules_LLM_revised_engine(self, rules, srouce_entities, grounded_relations):
        results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True

        entity_id_list = [k for k, v in srouce_entities.items()]

        if path is True:
            new_rules = {}
            for k, v in rules.items():
                if type(v)==list:
                    new_rules[k] = utils.string_to_path(v[0])
                else:
                    new_rules[k] = utils.string_to_path(v)
            rules = new_rules

        for entity in entity_id_list:

            entity_label = srouce_entities[entity]
            if entity_label not in rules.keys():
                continue

            # 注意,每次得到的grounded knowledge和result只会和一个topic entity有关!!!!
            grounded_reasoning_set = []
            if type(rules[entity_label][0])==str:
                for relation in rules[entity_label]:
                    grounded_reasoning_set.append(grounded_relations[relation])
            else:
                for relation in rules[entity_label][0]:
                    grounded_reasoning_set.append(grounded_relations[relation])

            if type(rules[entity_label][0])==str:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity, entity_label, rules[entity_label], grounded_reasoning_set)
            else:
                result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity, entity_label, rules[entity_label][0], grounded_reasoning_set)


            # 当前实体出发  如果非空,说明grounding成功, 加入路径
            if len(result_paths) > 0:
                results.extend(result_paths)

            # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
            else:
                return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict



        return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict


    # 0108 目前用的是这个
    def apply_rules_LLM_one_path_engine(self, rules, entity_id_label, grounded_relations):
        # results = []
        result_paths = []
        grounded_knowledge_current = []
        ungrounded_neighbor_relation_dict = {}
        path = True

        entity_id, entity_label = entity_id_label
        if path is True:
            if type(rules)==list:
                relation_path_array = utils.string_to_path(rules[0])
            else:
                relation_path_array = utils.string_to_path(rules)

        # grounded_reasoning_set 存储从前往后的 每一个grounded set
        grounded_reasoning_set = []
        for relation in relation_path_array:
            grounded_reasoning_set.append(grounded_relations[relation])

        # 这个代码 可以优化一下 因为现在是BFS,如果实体太大了 每个事实单独BFS 效率太低了
        # result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.bfs_with_rule_LLM_engine(entity_id, entity_label, relation_path_array, grounded_reasoning_set)
        result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = utils.grounding_with_engine(entity_id, entity_label, grounded_reasoning_set)

        # # 当前实体出发  如果非空,说明grounding成功, 加入路径
        # if len(result_paths) > 0:
        #     results.extend(result_paths)

        # # grounding出来是空的 那么就break, 重新, 根据返回结果来 refine 这条路径, 其他路径不变!
        # else:
        #     return results, result_paths, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict

        return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict


    def direct_answer(self, question_dict):
        graph = utils.build_graph(question_dict['graph'])
        entities = question_dict['q_entity']
        rules = question_dict['predicted_paths']
        prediction = []
        if len(rules) > 0:
            reasoning_paths = self.apply_rules(graph, rules, entities)
            for p in reasoning_paths:
                if len(p) > 0:
                    prediction.append(p[-1][-1])
        return prediction

    def grounding_relations(self, relation, question):
        # relation_path_candidates = items['relation_path_candidates']
        # question = items['question']
        # cwq[index]['relation_path_candidates']['grounded_relations'] = {}
        # cwq[index]['relation_path_candidates']['grounded_relations_no_q'] = {}

        # for key in relation_path_candidates['topic_entities']:
        #     for relations in relation_path_candidates['relation_paths'][key]:
        #         for rel in relations:
        #             if rel in cwq[index]['relation_path_candidates']['grounded_relations'].keys():
        #                 continue
        result= []
        relation_tokens = relation.replace("."," ").replace("_", " ").strip() + " "+ question
        hits = self.hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:5]
        for hit in hits:
            result.append(json.loads(self.corpus.doc(str(hit.docid)).raw())['rel_ori'])

        result_no_q= []
        relation_tokens = relation.replace("."," ").replace("_", " ").strip()
        hits = self.hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:5]
        for hit in hits:
            result_no_q.append(json.loads(self.corpus.doc(str(hit.docid)).raw())['rel_ori'])

        return result, result_no_q


    def ground_relations_from_predictions(self, reasoning_path_LLM_init, question):
        path=True
        # 把所有预测的关系先grounding一下
        rules = []
        if path is False:
            # 用str数组来存路径 效果差一些
            for keys in reasoning_path_LLM_init.keys():
                if type(reasoning_path_LLM_init[keys][0]) == str:
                    rules.append(reasoning_path_LLM_init[keys])
                else:
                    # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (因为我最开始实现的的plan 生成了多个)
                    rules.append(reasoning_path_LLM_init[keys][0])
        else:
            for keys in reasoning_path_LLM_init.keys():
                if type(reasoning_path_LLM_init[keys]) == str:
                    rules.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
                else:
                    # 这里的rules是LLM生成的路径 initial plan， 现在取每一个topic entity的top1  (因为我最开始实现的的plan 生成了多个)
                    rules.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))
        # 对所有路径的每一个关系 grounding （faiss）
        grounded_relations = {}
        for r in rules:
            for rel in r:
                relations, relations_no_q = self.grounding_relations(rel, question)
                if rel not in grounded_relations.keys():
                    grounded_relations[rel] = relations_no_q
                else:
                    grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))

        return grounded_relations


    def get_graph_knowledge(self, question_dict, reasoning_path_LLM):
        question = question_dict['question']
        if not question.endswith('?'):
            question += '?'

        if self.add_rule:
            graph = utils.build_graph(question_dict['graph'])
            entities = question_dict['q_entity']
            if self.use_true:
                rules = question_dict['ground_paths']
            elif self.use_random:
                _, rules = utils.get_random_paths(entities, graph)
            else:
                rules = question_dict['predicted_paths']
            # 这个rules是RoG预测的planning

            # if len(rules) > 0:
            if len(reasoning_path_LLM.keys()) > 0:
                # 这里的rules是LLM生成的路径 plan， 现在取每一个topic的top1
                rules = []
                for keys in reasoning_path_LLM:
                    rules.append(reasoning_path_LLM[keys][0])

                reasoning_paths = self.apply_rules_LLM(graph, rules, entities, reasoning_path_LLM['grounded_relations'])
                lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])
            else:
                lists_of_paths = []

        return reasoning_paths, lists_of_paths


    # def run_llm(self, prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-4-32k-20230321"):
    def run_llm(self, prompt, temperature, max_tokens, opeani_api_keys, engine="gpt-35-turbo-16k-20230613"):
        if "llama" not in engine.lower():
            openai.api_type = "azure"
            openai.api_base = "https://cloudgpt-openai.azure-api.net/"
            openai.api_version = "2023-07-01-preview"
            # to maintain token freshness, we need to acquire a new token every time we use the API
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
                if "gpt-4" in engine:
                    messages[-1] = {"role":"user","content": prompt[:32767]}
                    time.sleep(10)

                else:
                    messages[-1] = {"role":"user","content": prompt[:16384]}
                    time.sleep(5)
                print(len(messages[-1]["content"]))

        # print("end openai")
        return result


    def LLM_refine_agent(self, llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, current_prompt_agent, agent_time):
        # 初始路径 refine之前
        init_path = reasoning_path_LLM_init[entity_label]
        if type(init_path) == list:
            init_path=init_path[0]

        grounded_know = []
        ungrounded_cand_rel = {}
        max_grounded_len = 0
        thought = ""

        # 已有的知识有两种取法 一种是只要最长的(断掉的开始), 还有一种是全部从0到最长的都取
        if len(grounded_knowledge_current) > 0:
            max_grounded_len = grounded_knowledge_current[-1][-1]

        # 已有的知识,当前路径     这里可以有一个优化, 同类grounding对的知识     是不是取一个就够了????
        if len(grounded_knowledge_current) < 25:
            for know in grounded_knowledge_current:
                # 1. 只要最长的知识
                if know[-1] == max_grounded_len:
                    grounded_know.append(know[1])
                    node_label = utils.id2entity_name_or_type_en(know[0])
                    if node_label in ungrounded_neighbor_relation_dict.keys():
                        ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                # 2. 所有长度知识都要
                # grounded_know.append(know[1])
                # ungrounded_cand_rel = ungrounded_neighbor_relation_dict
        else:
            # 非CVT节点
            for i in grounded_knowledge_current:
                node_label = utils.id2entity_name_or_type_en(i[0])
                if node_label.startswith("m.")==False and i[2]!=0 and i[2]==max_grounded_len:
                    if node_label in ungrounded_neighbor_relation_dict.keys():
                        ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                    grounded_know.append(i[1])

            # 后续可以考虑根据相似度排序!!!!!
            if len(grounded_know) > 15 :
                # 相似度排序
                # grounded_know = utils.similar_search_list(question, [utils.path_to_string(know) for know in grounded_know])[:25]
                grounded_know = random.sample(grounded_know, 15)

            # cvt可能很多  全部处理成 <cvt></cvt>.
            cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0 and i[2]==max_grounded_len]
            if len(cvt_know) > 10:
                # cand_cvt = utils.similar_search_list(question, [utils.path_to_string(i[1]) for i in cvt_know])[:25]
                cvt_know = random.sample(cvt_know, 10)
            for cvt in cvt_know:
                if cvt[0] in ungrounded_neighbor_relation_dict.keys():
                    # cvt的label就是本身 不用转化
                    ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
                grounded_know.append(cvt[1])

        grounded_know = [" -> ".join([i if not i.startswith("m.") else "<cvt></cvt>" for i in utils.path_to_string(knowledge).split(" -> ")]) for knowledge in grounded_know]
        grounded_know = list(set(grounded_know))
        grounded_know_string = "\n".join(grounded_know)

        # candidate relation用集合方式 不用dict方式 尝试一下
        candidate_rel = []
        for k, v in ungrounded_cand_rel.items():
            candidate_rel.extend(v)
        candidate_rel = list(set(candidate_rel))

        # 关系给太多会爆炸 超过35随机抽35   这里可以按照和问题相似度排序!!!!!!
        if len(candidate_rel) > 35:
            candidate_rel = utils.similar_search_list(question, candidate_rel)[:35]
            # candidate_rel = random.sample(candidate_rel, 50)

        candidate_rel.sort()
        if agent_time==1:
            prompts = refine_agent_prompt  + "Question: " + question + "\n\nInitial Path: " + str(init_path) + "\nGrounded Knowledge " + str(agent_time) + ": " + grounded_know_string +"\nCandidate Relations" + str(agent_time) + ": " + str(candidate_rel) + "\n\nGoal:"
        else:
            prompts = current_prompt_agent + "\n\nGrounded Knowledge " + str(agent_time) + ": " + grounded_know_string +"\nCandidate Relations" + str(agent_time) + ": " + str(candidate_rel) + "\n\nGoal:"

        while refine_time <= 5:
            response = self.run_llm(prompts, temperature=0.4, max_tokens=4096, opeani_api_keys="", engine=llm_engine)
            try:
                refine_time+=1
                if "Refined Path" in response:
                    current_prompt_agent = prompts + response.split("Refined Path")[0]
                    function_calls = response.split("Refined Path")[0].strip().split("Function Call:")[-1].strip().strip("\"").strip()
                elif "Function Call:":
                    current_prompt_agent = prompts + response
                    function_calls = response.split("Function Call:")[-1].strip().strip("\"").strip()
                else:
                    print("bad call")
                    print(response)
                    raise ValueError("bad function call")

                functions = function_calls.split("\n")
                new_path = init_path

                for fun in functions:
                    if fun.startswith("replace_relation(") and fun.endswith(")"):
                        fun = fun.replace("replace_relation(","").replace(")", "").strip()
                        origin_relation = fun.split(",")[0].strip().strip("\'").strip("\"").strip()
                        refine_relation = fun.split(",")[-1].strip().strip("\'").strip("\"").strip()
                        new_path = new_path.replace(origin_relation, refine_relation)
                    elif fun.startswith("trim_relation(") and fun.endswith(")"):
                        fun = fun.replace("trim_relation(","").replace(")", "").strip()
                        relation = fun.strip().strip("\'").strip("\"").strip()
                        start_index = new_path.find("-> "+relation)
                        if start_index==-1:
                            start_index = new_path.find("->"+relation)
                            if start_index==-1:
                                print("bad function call")
                                print(functions)
                                raise ValueError("bad function call")
                        new_path = new_path[:start_index].strip()
                    elif fun.startswith("add_relation(") and fun.endswith(")"):
                        fun = fun.replace("add_relation(","").replace(")", "").strip()
                        relation = fun.strip().strip("\'").strip("\"").strip()
                        if relation in new_path:
                            print("bad call")
                            print(response)
                            raise ValueError("bad function call")

                        new_path = new_path.strip() + " -> " + relation
                    else:
                        print("bad function call")
                        print(functions)
                        raise ValueError("bad function call")

                if new_path==init_path:
                    print(functions)
                    raise ValueError("function call no changing origin plan")

                if "->" not in new_path or entity_label not in new_path:
                    print("****************************************************************")
                    print(functions)
                    print("new path:",new_path)
                    print("****************************************************************")
                    raise ValueError("function call no changing origin plan")

                reasoning_path_LLM_init[entity_label] = new_path
                current_prompt_agent += "Refined Path "+ str(agent_time) +": " + new_path
                agent_time += 1
                break
            except:
                print("*****************************************************************************************")
                print(response)
                print("****************************************************************************************")
                time.sleep(5)

        return reasoning_path_LLM_init, refine_time, thought, current_prompt_agent, agent_time



    def LLM_refine(self, args, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time):
        # 初始路径 refine之前
        init_path = reasoning_path_LLM_init[entity_label]
        if type(init_path) == list:
            init_path=init_path[0]

        grounded_know = []
        ungrounded_cand_rel = {}
        max_grounded_len = 0
        thought = ""
        cvt_ending = False

        if len(grounded_knowledge_current) > 0:
            max_grounded_len = grounded_knowledge_current[-1][-1]

        # 已有的知识,当前路径  这里可以有一个优化, 同类grounding对的知识    是不是取一个就够了????
        for know in grounded_knowledge_current:
            node_label = utils.id2entity_name_or_type_en(know[0])
            if node_label.startswith("m.")==False and know[2]!=0 and know[2]==max_grounded_len:
                if node_label in ungrounded_neighbor_relation_dict.keys():
                    ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                grounded_know.append(know[1])
            if know[2]==max_grounded_len and node_label.startswith("m."):
                cvt_ending = True

        # 可以考虑根据相似度排序!!!!!
        if len(grounded_know) > 15 :
            # 相似度排序
            # grounded_know = utils.similar_search_list(question, [utils.path_to_string(know) for know in grounded_know])[:25]
            grounded_know = random.sample(grounded_know, 15)

        # cvt可能很多  全部处理成 <cvt></cvt>.
        cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0 and i[2]==max_grounded_len]
        if len(cvt_know) > 10:
            # cand_cvt = utils.similar_search_list(question, [utils.path_to_string(i[1]) for i in cvt_know])[:25]
            cvt_know = random.sample(cvt_know, 10)
        for cvt in cvt_know:
            if cvt[0] in ungrounded_neighbor_relation_dict.keys():
                # cvt的label就是本身 不用转化
                ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
            grounded_know.append(cvt[1])

        grounded_know = [" -> ".join([i if not i.startswith("m.") else "<cvt></cvt>" for i in utils.path_to_string(knowledge).split(" -> ")]) for knowledge in grounded_know]
        grounded_know = list(set(grounded_know))
        grounded_know_string = "\n".join(grounded_know)

        if len(grounded_know)==0 and len(ungrounded_neighbor_relation_dict)>0:
            ungrounded_cand_rel = ungrounded_neighbor_relation_dict

        # candidate relation用集合方式 不用dict方式 尝试一下
        candidate_rel = []
        for k, v in ungrounded_cand_rel.items():
            candidate_rel.extend(v)
        candidate_rel = list(set(candidate_rel))

        # 关系给太多会爆炸 超过35随机抽35   这里可以按照和问题相似度排序!!!!!!
        if len(candidate_rel) > 35:
            candidate_rel = utils.similar_search_list(question, candidate_rel)[:35]
            # candidate_rel = random.sample(candidate_rel, 50)
        candidate_rel.sort()        

        if 'err_msg' in args.refine_output:
            err_msg_list = []
            if cvt_ending:
                err_msg_list.append("<cvt></cvt> in the end.")
            relation_elements = init_path.split(" -> ")[1:]
            if max_grounded_len < len(relation_elements):
                ungrounded_relation = relation_elements[max_grounded_len]
                err_msg_list.append(f"relation \"{ungrounded_relation}\" not instantiated.")
            err_msg = ""
            for index, msg in enumerate(err_msg_list):
                err_msg+= str(index+1)+". "+msg +"\n"

        # prompts = refine_prompt_path_one_path_1224  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel) + "\nThought:"
        # prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_1229_2052  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"
        # prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_0103  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"
        # prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_0109  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nInstantiate Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"
        if args.refine_output == 'function':
            prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_0109  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel) + "\n>>>> Correcting Function\nGoal:"
        elif args.refine_output == 'sequence':
            prompts = refine_prompt_path_one_path_seq_cvt_deal_new_goal_progress_0109  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel) + "\n>>>> Corrected Path\nGoal:"
        elif args.refine_output == 'sequence_err_msg':
            # prompts = refine_prompt_path_one_path_seq_cvt_deal_new_goal_progress_err_msg0110  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Error Message\n" + err_msg + ">>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel)  + "\n>>>> Corrected Path"
            prompts = refine_prompt_path_one_path_seq_cvt_deal_new_goal_progress_err_msg_no_thought0110  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Error Message\n" + err_msg + ">>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel)  + "\n>>>> Corrected Path"
        elif args.refine_output == 'function_err_msg':
            # prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_err_msg_thought0110  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Error Message\n" + err_msg + ">>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel)  + "\n>>>> Correcting Function"
            prompts = refine_prompt_path_one_path_func_cvt_deal_new_goal_progress_err_msg_no_thought0110  + "Question: " + question + "\nInitial Path:" + str(init_path) + "\n>>>> Error Message\n" + err_msg + ">>>> Instantiation Message\nInstantiate Paths:" + grounded_know_string +"\nCandidate Relations:" + str(candidate_rel)  + "\n>>>> Correcting Function"
        
        # prompts = refine_agent_prompt  + "\nQuestion: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"

        while refine_time <= 8:
            response = self.run_llm(prompts, temperature=args.temperature_refine, max_tokens=4096, opeani_api_keys="", engine=args.llm_engine)
            try:
                refine_time+=1
                if "function" in args.refine_output:
                    if 'Thouhght' in prompts:
                        function_calls = response.strip().strip("\"").strip()
                    else:
                        function_calls = response.split("Correcting Function:")[-1].strip().strip("\"").strip()
                    functions = function_calls.split("\n")
                    new_path = init_path
                    for fun in functions:
                        if fun.startswith("replace_relation(") and fun.endswith(")"):
                            fun = fun.replace("replace_relation(","").replace(")", "").strip()
                            origin_relation = fun.split(",")[0].strip().strip("\'").strip("\"").strip()
                            refine_relation = fun.split(",")[-1].strip().strip("\'").strip("\"").strip()
                            if origin_relation not in init_path:
                                print("****************************************************************")
                                print(functions)
                                print("****************************************************************")
                                raise ValueError("bad function call:  replaced relation not in path!")
                            new_path = new_path.replace(origin_relation, refine_relation).strip()
                        elif fun.startswith("remove_relation(") and fun.endswith(")"):
                            fun = fun.replace("remove_relation(","").replace(")", "").strip()
                            relation = fun.strip().strip("\'").strip("\"").strip()

                            start_index = new_path.find(" -> "+relation)
                            if start_index==-1:
                                print("****************************************************************")
                                print(functions)
                                print("****************************************************************")
                                raise ValueError("bad function call:  remove_relation relation not in path!")

                            new_path = new_path[:start_index] + new_path[start_index+len(relation + " -> "):]
                            new_path = new_path.replace("  ", " ").strip()

                        elif fun.startswith("add_relation(") and fun.endswith(")"):
                            fun = fun.replace("add_relation(","").replace(")", "").strip()
                            # relation = fun.strip().strip("\'").strip("\"").strip()
                            # new_path = new_path.strip() + " -> " + relation

                            relation = fun.split(",")[0].strip().strip("\'").strip("\"").strip()
                            position = (",").join(fun.split(",")[1:]).strip().strip("\'").strip("\"").strip()

                            start_index = new_path.find(position)
                            if start_index==-1:
                                start_index = new_path.find(position)
                                if start_index==-1:
                                    print("****************************************************************")
                                    print(functions)
                                    print("****************************************************************")
                                    raise ValueError("bad function call: add_relation position not in path")
                            new_path = new_path[:start_index+len(position)] + " -> " + relation + new_path[start_index+len(position):]
                            new_path = new_path.replace("  ", " ").strip()
                        else:
                            print("****************************************************************")
                            print(functions)
                            raise ValueError("NO given function called")
                        
                elif "sequence" in args.refine_output:
                    # 直接生成Refined Path
                    new_path = response.split("Final Path:")[-1].strip().strip("\"").strip()
                    thought = response
                    if entity_label not in new_path or "->" not in new_path:
                        raise ValueError("entity_label or -> is not in path")
                    reasoning_path_LLM_init[entity_label] = new_path                  

                elif args.refine_output == "dict":
                    new_reasoning_path_LLM_init=eval(response.split("Refined Path:")[-1].strip())
                    if type(new_reasoning_path_LLM_init) != dict:
                        raise ValueError("GPT generate type no match, regenerate")

                    if len(new_reasoning_path_LLM_init.keys()) == 0:
                        raise ValueError("GPT generate topics entities no match, regenerate")

                    for k, v in new_reasoning_path_LLM_init.items():
                        if type(v) != list:
                            raise ValueError("GPT generate format no match, regenerate")

                    for key in new_reasoning_path_LLM_init.keys():
                        if reasoning_path_LLM_init[key] == new_reasoning_path_LLM_init[key]:
                            print(response)
                            print("****************************************************************************************")
                        reasoning_path_LLM_init[key]=new_reasoning_path_LLM_init[key]
                    else:
                        reasoning_path_LLM_init = new_reasoning_path_LLM_init
                    break

                if new_path == init_path:
                    print("****************************************************************")
                    # print("----------new path no changing-----------:",functions)
                    print("----------new path  -----------:", new_path)
                    print("****************************************************************")
                    raise ValueError("no changing origin plan")

                if "->" not in new_path or entity_label not in new_path:
                    print("****************************************************************")
                    # print(functions)
                    print("----------new path:", new_path)
                    print("****************************************************************")
                    raise ValueError("no changing origin plan")

                elements = new_path.split(" -> ")
                if len(list(set(elements))) < len(elements):
                    print("****************************************************************")
                    # print(functions)
                    print("----------new path:", new_path)
                    print("****************************************************************")
                    raise ValueError("same relation in path")
                if len(elements) > 5:
                    print("****************************************************************")
                    # print(functions)
                    print("----------new path:", new_path)
                    print("****************************************************************")
                    raise ValueError("path too long!!!!")   
                
                reasoning_path_LLM_init[entity_label] = new_path
                thought = response + " new_path:" + new_path
                break
            except Exception as e:
                print(e)
                print("*****************************************************************************************")
                print()
                time.sleep(1)

        return reasoning_path_LLM_init, refine_time, thought


    def LLM_refine_and_stop_condition(self, llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, End_loop_cur_path, Ends_with_cvt):
        # 初始路径 refine之前
        init_path = reasoning_path_LLM_init[entity_label]
        if type(init_path) == list:
            init_path=init_path[0]

        grounded_know = []
        ungrounded_cand_rel = {}
        max_grounded_len = 0
        thought = ""
        # 已有的知识, 其他topic的路径   (加不加看效果考虑)
        # for entity, knowledge in grounded_revised_knowledge.items():
        #     if len(knowledge)>0:
        #         grounded_know.append(knowledge)

        # 已有的知识有两种取法 一种是只要最长的(断掉的开始), 还有一种是全部从0到最长的都取
        if len(grounded_knowledge_current) > 0:
            max_grounded_len = grounded_knowledge_current[-1][-1]

        # 已有的知识,当前路径     这里可以有一个优化, 同类grounding对的知识     是不是取一个就够了????
        if len(grounded_knowledge_current) < 25:
            for know in grounded_knowledge_current:
                # 1. 只要最长的知识
                if know[-1] == max_grounded_len:
                    grounded_know.append(know[1])
                    node_label = utils.id2entity_name_or_type_en(know[0])
                    if node_label in ungrounded_neighbor_relation_dict.keys():
                        ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                # 2. 所有长度知识都要
                # grounded_know.append(know[1])
                # ungrounded_cand_rel = ungrounded_neighbor_relation_dict
        else:
            # 非CVT节点
            for i in grounded_knowledge_current:
                node_label = utils.id2entity_name_or_type_en(i[0])
                if node_label.startswith("m.")==False and i[2]!=0 and i[2]==max_grounded_len:
                    if node_label in ungrounded_neighbor_relation_dict.keys():
                        ungrounded_cand_rel[node_label] = ungrounded_neighbor_relation_dict[node_label]
                    grounded_know.append(i[1])

            # 后续可以考虑根据相似度排序!!!!!
            if len(grounded_know) > 15 :
                # 相似度排序
                # grounded_know = utils.similar_search_list(question, [utils.path_to_string(know) for know in grounded_know])[:25]
                grounded_know = random.sample(grounded_know, 15)

            # # cvt可能很多 随机抽10个吧
            # cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0 and i[2]==max_grounded_len]
            # if len(cvt_know) > 10:
            #     # cand_cvt = utils.similar_search_list(question, [utils.path_to_string(i[1]) for i in cvt_know])[:25]
            #     cand_cvt = random.sample(cvt_know, 10)
            # else:
            #     cand_cvt = cvt_know

            # for cvt in cand_cvt:
            #     if cvt[0] in ungrounded_neighbor_relation_dict.keys():
            #         # cvt的label就是本身 不用转化
            #         ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
            #     grounded_know.append(cvt[1])


            # cvt可能很多  全部处理成 <cvt></cvt>.
            cvt_know = [(i[0], i[1]) for i in grounded_knowledge_current if utils.id2entity_name_or_type_en(i[0]).startswith("m.") and len(i[1])>0 and i[2]==max_grounded_len]
            if len(cvt_know) > 10:
                # cand_cvt = utils.similar_search_list(question, [utils.path_to_string(i[1]) for i in cvt_know])[:25]
                cvt_know = random.sample(cvt_know, 10)
            for cvt in cvt_know:
                if cvt[0] in ungrounded_neighbor_relation_dict.keys():
                    # cvt的label就是本身 不用转化
                    ungrounded_cand_rel[cvt[0]] = ungrounded_neighbor_relation_dict[cvt[0]]
                grounded_know.append(cvt[1])

        grounded_know = [" -> ".join([i if not i.startswith("m.") else "<cvt></cvt>" for i in utils.path_to_string(knowledge).split(" -> ")]) for knowledge in grounded_know]
        grounded_know = list(set(grounded_know))
        grounded_know_string = "\n".join(grounded_know)

        # candidate relation用集合方式 不用dict方式 尝试一下
        candidate_rel = []
        for k, v in ungrounded_cand_rel.items():
            candidate_rel.extend(v)
        candidate_rel = list(set(candidate_rel))

        # 关系给太多会爆炸 超过35随机抽35   这里可以按照和问题相似度排序!!!!!!
        if len(candidate_rel) > 35:
            candidate_rel = utils.similar_search_list(question, candidate_rel)[:35]
            # candidate_rel = random.sample(candidate_rel, 50)

        candidate_rel.sort()

        # grounded_know_string = ""
        # for know in grounded_know:
        #     if know == []:
        #         continue
        #     grounded_know_string+=utils.path_to_string(know) + "\n"

        # prompts = refine_prompt_path_one_path_1222  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(ungrounded_cand_rel) + "\nThought:"
        # prompts = refine_prompt_path_one_path_add_stop_condition_1227  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nThought:"
        # prompts = refine_prompt_path_one_path_add_stop_condition_func_1227  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"
        # prompts = refine_prompt_path_one_path_add_stop_condition_func_cvt_deal_1228  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"
        prompts = refine_prompt_path_one_path_add_stop_condition_func_cvt_deal_goal_progress_1229_new  + "Question: " + question + "\n\nInitial Path:" + str(init_path) + "\n\nGrounded Knowledge:" + grounded_know_string +"\n\nCandidate Relations:" + str(candidate_rel) + "\n\nGoal:"

        # call_time=0
        while refine_time <= 5:
            response = self.run_llm(prompts, temperature=0.2, max_tokens=4096, opeani_api_keys="", engine=llm_engine)
            try:
                refine_time += 1
                function_calls = response.split("Function Call:")[-1].strip().strip("\"").strip()
                if "stop_refine()" in function_calls:
                    if Ends_with_cvt:
                        print("Ends with CVT, but output stop")
                        raise ValueError("Ends with CVT, but output stop")

                    End_loop_cur_path = True
                    thought = response
                    return reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought

                functions = function_calls.split("\n")
                new_path = init_path

                for fun in functions:
                    if fun.startswith("replace_relation(") and fun.endswith(")"):
                        fun = fun.replace("replace_relation(","").replace(")", "").strip()
                        origin_relation = fun.split(",")[0].strip().strip("\'").strip("\"").strip()
                        refine_relation = fun.split(",")[-1].strip().strip("\'").strip("\"").strip()
                        new_path = new_path.replace(origin_relation, refine_relation)
                    elif fun.startswith("trim_relation(") and fun.endswith(")"):
                        fun = fun.replace("trim_relation(","").replace(")", "").strip()
                        relation = fun.strip().strip("\'").strip("\"").strip()
                        start_index = new_path.find("-> "+relation)
                        if start_index==-1:
                            start_index = new_path.find("->"+relation)
                            if start_index==-1:
                                print("bad function call")
                                print(functions)
                                raise ValueError("bad function call")
                        new_path = new_path[:start_index].strip()
                    elif fun.startswith("add_relation(") and fun.endswith(")"):
                        fun = fun.replace("add_relation(","").replace(")", "").strip()
                        relation = fun.strip().strip("\'").strip("\"").strip()
                        new_path = new_path.strip() + " -> " + relation
                    else:
                        print("bad function call")
                        print(functions)
                        raise ValueError("bad function call")

                if new_path==init_path:
                    print(functions)
                    raise ValueError("function call no changing origin plan")

                if "->" not in new_path:
                    print("****************************************************************")
                    print(functions)
                    print("new path:",new_path)
                    print("****************************************************************")
                    raise ValueError("function call no changing origin plan")

                reasoning_path_LLM_init[entity_label] = new_path

                # if "***STOP REFINE***" in response:
                #     if Ends_with_cvt:
                #         print("Ends with CVT, but output stop")
                #         raise ValueError("Ends with CVT, but output stop")

                #     End_loop_cur_path = True
                #     thought = response
                #     return reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought

                # new_rule_path = response.split("Refined Path:")[-1].strip().strip("\"").strip()
                # thought = response
                # if entity_label not in new_rule_path or "->" not in new_rule_path:
                #     print()
                #     print("entity_label or -> is not in path")
                #     raise ValueError("entity_label or -> is not in path")

                # # 没什么变化 不用refine了
                # if init_path == new_rule_path:
                #     if refine_time > 5:
                #         End_loop_cur_path = True
                #         thought = response
                #         return reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought
                #     else:
                #         refine_time +=3
                #         print("same path as before")
                #         raise ValueError("same path as before")
                # reasoning_path_LLM_init[entity_label] = new_rule_path




                # new_reasoning_path_LLM_init=eval(response.split("Refined Path:")[-1].strip())
                # if type(new_reasoning_path_LLM_init) != dict:
                #     raise ValueError("GPT generate type no match, regenerate")

                # if len(new_reasoning_path_LLM_init.keys()) == 0:
                #     raise ValueError("GPT generate topics entities no match, regenerate")

                # if not path:
                #     for k, v in new_reasoning_path_LLM_init.items():
                #         if type(v) != list:
                #             raise ValueError("GPT generate format no match, regenerate")
                # refine_time += 1

                # if one_path is True:
                #     for key in new_reasoning_path_LLM_init.keys():
                #         if reasoning_path_LLM_init[key] == new_reasoning_path_LLM_init[key]:
                #             refine_time += 10
                #             print(response)
                #             print("****************************************************************************************")
                #         reasoning_path_LLM_init[key]=new_reasoning_path_LLM_init[key]
                # else:
                #     reasoning_path_LLM_init = new_reasoning_path_LLM_init


                break
            except:
                print("****************************************************************************************")
                print(response)
                print("****************************************************************************************")
                time.sleep(3)

        return reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought


    def merge_different_path(self, grounded_revised_knowledge, reasoning_paths, lists_of_paths):
        print("**********************merge*****************************")
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

                # 说明两个topic entity的知识集合有交集  每次有交集就先给他们取个交集
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
                    # 没有交集 并且当前路径太长了，  想办法剪枝一下
                    if len(reasoning_paths) > 30:
                        for k, v in knowledeg_len_dict.items():
                            # 这个实体开头的知识太多了 并且没有交集,说明他八成没用, 把这个实体开头的路径、知识 全删了
                            if v > 50:
                                new_reasoning_paths = []
                                lists_of_paths = []
                                for path in reasoning_paths:
                                    string_path = str(path).strip("[").strip("(").strip("\'").strip("\"").strip()
                                    if not string_path.startswith(k):
                                        new_reasoning_paths.append(path)
                                        lists_of_paths.append(utils.path_to_string(path))

                                reasoning_paths = new_reasoning_paths

        return reasoning_paths, lists_of_paths


    # Refine framework
    def get_graph_knowledge_LLM_revised_engine(self, args, question_dict):
        reasoning_path_LLM_init = question_dict['relation_path_candidates']
        question = question_dict[get_question_string(args.dataset)]
        entities = question_dict['topic_entity']
        if not question.endswith('?'):
            question += '?'

        print("Question:", question)
        path = True
        one_path = True
        refine_time = 0

        # 开始进入框架   可能会套两层while循环 外层对所有实体（整个知识）判断path是否要继续refine。 内层对单个实体的一条路径判断是否需要继续refine
        # while True:
        # 确保有初始路径 or refine过的路径
        if len(reasoning_path_LLM_init.keys()) > 0:
            # 准备用这个来存所有的路径 最后merge
            grounded_revised_knowledge = {}
            len_of_grounded_knowledge = {}
            len_of_predict_knowledge = {}
            reasoning_paths = []
            thought = ""
            lists_of_paths = []
            predict_path = {}
            current_prompt_agent=""
            agent_time = 1

            # 获取对所有路径上的relation 做搜索召回 （top5） 结果是dict {relation: grounded array}

            # 对每一个entity 引导的路径进行grounding
            for entity_id, entity_label in entities.items():
                if entity_label not in reasoning_path_LLM_init.keys():
                    continue
                print("Topic entity: ",entity_label)
                # 每一个entity都要进入refine loop
                while True:
                    grounded_relations = self.ground_relations_from_predictions(reasoning_path_LLM_init, question)

                    # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                    result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = self.apply_rules_LLM_one_path_engine(reasoning_path_LLM_init[entity_label], [entity_id,entity_label], grounded_relations)

                    print("cur refine time", refine_time)
                    print("len of result paths", len(result_paths))
                    print("len of grounded knowledge current", len(grounded_knowledge_current))
                    # print("ungrounded neighbor relation dict", ungrounded_neighbor_relation_dict)

                    # record current states
                    max_path_len = grounded_knowledge_current[-1][-1]
                    print("max len of grounded knowledge current", max_path_len)
                    if entity_label not in predict_path.keys():
                        # 注意！！！初始状态下 reasoning_path_LLM_init[entity_label]是个数组， 后面refine过程中会变成str 。历史原因 抱歉
                        predict_path[entity_label] = [reasoning_path_LLM_init[entity_label][0]]
                        len_of_grounded_knowledge[entity_label] = [max_path_len]
                        print("len of predict path", len(reasoning_path_LLM_init[entity_label][0].split("->"))-1)
                        len_of_predict_knowledge[entity_label] = [len(reasoning_path_LLM_init[entity_label][0].split("->"))-1]
                    else:
                        len_of_grounded_knowledge[entity_label].append(max_path_len)
                        predict_path[entity_label].append(reasoning_path_LLM_init[entity_label])
                        print("len of predict path", len(reasoning_path_LLM_init[entity_label].split("->"))-1)
                        len_of_predict_knowledge[entity_label].append(len(reasoning_path_LLM_init[entity_label].split("->"))-1)

                    End_loop_cur_path = True
                    Ends_with_cvt = False

                    # # 硬性判断什么时候停
                    if len(result_paths) > 0:
                        if max_path_len == 0:
                            End_loop_cur_path = False
                            
                        for path in result_paths:
                            if len(path) < max_path_len:
                                continue
                            # 最后一个知识以m.结尾 说明遇到了空白节点
                            if path[-1][-1].startswith("m.") or path[-1][-1].startswith("g."):
                                End_loop_cur_path=False
                                # Ends_with_cvt = True
                                break
                    else:
                        End_loop_cur_path = False

                    # # llm refine and stop condition
                    if End_loop_cur_path == False:
                        # 硬性停
                        # reasoning_path_LLM_init, refine_time, thought, current_prompt_agent, agent_time = self.LLM_refine_agent(llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, current_prompt_agent, agent_time)
                        reasoning_path_LLM_init, refine_time, thought = self.LLM_refine(args, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time)
                    #     reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought = self.LLM_refine_and_stop_condition(llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, End_loop_cur_path, Ends_with_cvt)

                    if End_loop_cur_path or refine_time >= 8:
                        reasoning_paths.extend(result_paths)
                        grounded_revised_knowledge[entity_label] = result_paths
                        lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]

                        # TODO这里应该设置一个开关 ： grounding可能失败了，但是grounding路上的知识可能是有用的，为了分析数据（init path的好坏） 可以关掉； 为了看init path qa的效果 可以开启
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
                            # 路径集合
                            lists_of_paths = list(set(lists_of_paths))
                        break

            # merge一下
            if len(entities) > 1:
                 reasoning_paths, lists_of_paths = self.merge_different_path(grounded_revised_knowledge, reasoning_paths, lists_of_paths)

        return reasoning_paths, lists_of_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path


    # only init path framework
    def get_graph_knowledge_LLM_init_plan(self, args, question_dict):
        reasoning_path_LLM_init = question_dict['relation_path_candidates']
        question = question_dict['question']
        entities = question_dict['topic_entity']
        if not question.endswith('?'):
            question += '?'
        print("Question:", question)
        # path表示用"->"分割的路径,prompt的一种尝试  如果用数组的话效果会差一些
        path = True

        # 确保有初始路径 or refine过的路径
        if len(reasoning_path_LLM_init.keys()) > 0:
            # 准备用这个来存所有的路径 最后merge
            grounded_revised_knowledge = {}
            len_of_predict_knowledge = {}
            len_of_grounded_knowledge = {}
            predict_path = {}
            reasoning_paths = []
            thought = ""
            lists_of_paths = []

            # 对每一个entity 引导的路径进行grounding
            for entity_id, entity_label in entities.items():
                if entity_label not in reasoning_path_LLM_init.keys():
                    continue
                print("Topic entity: ",entity_label)
                # 获取对所有路径上的relation 做搜索召回 （top5） 结果是dict {relation: grounded array}
                grounded_relations = self.ground_relations_from_predictions(reasoning_path_LLM_init, question)
                # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                result_paths, grounded_knowledge_current, _ = self.apply_rules_LLM_one_path_engine(reasoning_path_LLM_init[entity_label], [entity_id,entity_label], grounded_relations)

                print("len of result paths", len(result_paths))
                print("len of grounded knowledge current", len(grounded_knowledge_current))

                # record current states
                max_path_len = grounded_knowledge_current[-1][-1]
                print("max len of grounded knowledge current", max_path_len)
                if entity_label not in predict_path.keys():
                    # 注意！！！初始状态下 reasoning_path_LLM_init[entity_label]是个数组， 后面refine过程中会变成str 。历史原因 抱歉
                    predict_path[entity_label] = [reasoning_path_LLM_init[entity_label][0]]
                    len_of_grounded_knowledge[entity_label] = [max_path_len]
                    print("len of predict path", len(reasoning_path_LLM_init[entity_label][0].split("->"))-1)
                    len_of_predict_knowledge[entity_label] = [len(reasoning_path_LLM_init[entity_label][0].split("->"))-1]
                else:
                    len_of_grounded_knowledge[entity_label].append(max_path_len)
                    predict_path[entity_label].append(reasoning_path_LLM_init[entity_label])
                    print("len of predict path", len(reasoning_path_LLM_init[entity_label].split("->"))-1)
                    len_of_predict_knowledge[entity_label].append(len(reasoning_path_LLM_init[entity_label].split("->"))-1)

                if len(result_paths) > 0:
                    reasoning_paths.extend(result_paths)
                    grounded_revised_knowledge[entity_label] = result_paths
                    lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]

                # TODO这里应该设置一个开关 ： grounding可能失败了，但是grounding路上的知识可能是有用的，为了分析数据（init path的好坏） 可以关掉； 为了看init path qa的效果 可以开启
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
                    # 路径集合
                    lists_of_paths = list(set(lists_of_paths))

            # merging module
            if len(entities) > 1:
                reasoning_paths, lists_of_paths = self.merge_different_path(grounded_revised_knowledge, reasoning_paths, lists_of_paths)

        return reasoning_paths, lists_of_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path


    # empty init path framework
    def get_graph_knowledge_LLM_empty_init(self, args, question_dict):
        reasoning_path_LLM_init = question_dict['relation_path_candidates']
        question = question_dict['question']
        entities = question_dict['topic_entity']
        if not question.endswith('?'):
            question += '?'

        print("Question:", question)
        # path表示用"->"分割的路径,prompt的一种尝试  如果用数组的话效果会差一些
        path = True
        refine_time = 0

        # 为了方便 懒得重新做一个文件了 直接清空吧（doge
        for k, v in reasoning_path_LLM_init.items():
            reasoning_path_LLM_init[k] = [k]

        # 确保有初始路径 or refine过的路径
        if len(reasoning_path_LLM_init.keys()) > 0:
            # 准备用这个来存所有的路径 最后merge
            grounded_revised_knowledge = {}
            len_of_predict_knowledge = {}
            len_of_grounded_knowledge = {}
            reasoning_paths = []
            thought = ""
            predict_path = {}
            lists_of_paths = []

            current_prompt_agent=""
            agent_time = 1

            # 获取对所有路径上的relation 做搜索召回 （top5） 结果是dict {relation: grounded array}

            # 对每一个entity 引导的路径进行grounding
            for entity_id, entity_label in entities.items():
                if entity_label not in reasoning_path_LLM_init.keys():
                    continue
                print("Topic entity: ",entity_label)
                # 每一个entity都要进入refine loop
                while True:
                    grounded_relations = self.ground_relations_from_predictions(reasoning_path_LLM_init, question)

                    if refine_time>0:
                        # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                        result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict = self.apply_rules_LLM_one_path_engine(reasoning_path_LLM_init[entity_label], [entity_id,entity_label], grounded_relations)
                    else:
                        result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict=[],[],{entity_label: utils.get_ent_one_hop_rel(entity_id)}

                    print("refine time", refine_time)
                    print("result paths", result_paths)

                    # record current states
                    max_path_len = grounded_knowledge_current[-1][-1]
                    print("max len of grounded knowledge current", max_path_len)
                    if entity_label not in predict_path.keys():
                        # 注意！！！初始状态下 reasoning_path_LLM_init[entity_label]是个数组， 后面refine过程中会变成str 。历史原因 抱歉
                        predict_path[entity_label] = [reasoning_path_LLM_init[entity_label][0]]
                        len_of_grounded_knowledge[entity_label] = [max_path_len]
                        print("len of predict path", len(reasoning_path_LLM_init[entity_label][0].split("->"))-1)
                        len_of_predict_knowledge[entity_label] = [len(reasoning_path_LLM_init[entity_label][0].split("->"))-1]
                    else:
                        len_of_grounded_knowledge[entity_label].append(max_path_len)
                        predict_path[entity_label].append(reasoning_path_LLM_init[entity_label])
                        print("len of predict path", len(reasoning_path_LLM_init[entity_label].split("->"))-1)
                        len_of_predict_knowledge[entity_label].append(len(reasoning_path_LLM_init[entity_label].split("->"))-1)

                    End_loop_cur_path = True
                    # # 硬性判断什么时候停
                    if len(result_paths) > 0:
                        max_path_len =  len(result_paths[-1])
                        if max_path_len == 0:
                            continue
                        for path in result_paths:
                            if len(path) < max_path_len:
                                continue
                            # 最后一个知识以m.结尾 说明遇到了空白节点
                            if path[-1][-1].startswith("m."):
                                End_loop_cur_path=False
                                # Ends_with_cvt = True
                    else:
                        End_loop_cur_path = False

                    # # llm refine and stop condition
                    # init path是空的 一开始一定要refine
                    if End_loop_cur_path == False or refine_time==0:
                        # 硬性停
                        # reasoning_path_LLM_init, refine_time, thought, current_prompt_agent, agent_time = self.LLM_refine_agent(llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, current_prompt_agent, agent_time)
                        reasoning_path_LLM_init, refine_time, thought = self.LLM_refine(args, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time)
                    #     reasoning_path_LLM_init, refine_time, End_loop_cur_path, thought = self.LLM_refine_and_stop_condition(llm_engine, reasoning_path_LLM_init, entity_label, grounded_knowledge_current, ungrounded_neighbor_relation_dict, question, refine_time, End_loop_cur_path, Ends_with_cvt)

                    if End_loop_cur_path or refine_time >= 8:
                        reasoning_paths.extend(result_paths)
                        grounded_revised_knowledge[entity_label] = result_paths
                        lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]

                        # 可以留下最长的grounded知识 可选!!!
                        # TODO这里应该设置一个开关 ： grounding可能失败了，但是grounding路上的知识可能是有用的，为了分析数据（init path的好坏） 可以关掉； 为了看init path qa的效果 可以开启
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
                            # 路径集合
                            lists_of_paths = list(set(lists_of_paths))
                        break

            # # TODO 遍历完了所有的路径 应该merge一下
            if len(entities) > 1:
                reasoning_paths, lists_of_paths = self.merge_different_path(grounded_revised_knowledge, reasoning_paths, lists_of_paths)

        return reasoning_paths, lists_of_paths, thought, len_of_predict_knowledge, len_of_grounded_knowledge, predict_path


    def get_graph_knowledge_LLM_revised(self, question_dict, reasoning_path_LLM_init):
        question = question_dict['question']
        if not question.endswith('?'):
            question += '?'

        graph = utils.build_graph(question_dict['graph'])
        entities = question_dict['q_entity']

        path = True
        one_path = True

        refine_time = 0
        # 这个rules是RoG预测的planning
        # if len(rules) > 0:
        while True:
            if len(reasoning_path_LLM_init.keys()) > 0:

                # 这里的rules是LLM生成的路径 plan， 现在取每一个topic的top1
                rules = []
                if path is False:
                    for keys in reasoning_path_LLM_init.keys():
                        if type(reasoning_path_LLM_init[keys][0]) == str:
                            rules.append(reasoning_path_LLM_init[keys])
                        else:
                            rules.append(reasoning_path_LLM_init[keys][0])

                else:
                    for keys in reasoning_path_LLM_init.keys():
                        if type(reasoning_path_LLM_init[keys]) == str:
                            rules.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
                        else:
                            rules.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))

                # grounding 每一个关系
                grounded_relations = {}
                for r in rules:
                    for rel in r:
                        relations, relations_no_q = self.grounding_relations(rel, question)
                        if rel not in grounded_relations.keys():
                            grounded_relations[rel] = relations_no_q
                        else:
                            grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))

                # grounding路径
                # result_path表示 grounding过程中的path,如果是空的,说明当前grounding遇到了问题,需要refine
                reasoning_paths, result_paths, entity, grounded_knowledge_current, ungrounded_neighbor_relation_dict = self.apply_rules_LLM_revised(graph, reasoning_path_LLM_init, entities, grounded_relations)

                if len(result_paths) > 0 or refine_time > 10:
                    lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                    if len(grounded_knowledge_current) > 0:
                        for grounded_path in grounded_knowledge_current:
                            string_path = utils.path_to_string(grounded_path[1])
                            if len(string_path) > 0:

                                if string_path not in lists_of_paths:
                                    lists_of_paths.append(string_path)

                                if len(reasoning_paths) == 0:
                                    reasoning_paths.append([])

                                reasoning_paths[0] += grounded_path[1]
                    # 路径集合
                    lists_of_paths = list(set(lists_of_paths))
                    # 知识集合
                    if len(reasoning_paths)>0:
                        reasoning_paths[0] = list(set(reasoning_paths[0]))
                    # for grounded_path in grounded_knowledge_current:
                    #     if len(reasoning_paths) == 0:
                    #         reasoning_paths.append([])
                    #     reasoning_paths[0] += grounded_path[1]

                    break
                else:
                    # llm_REVISE
                    init_path = {}

                    # 初始路径
                    if one_path is True:
                        if path is False:
                            if type(reasoning_path_LLM_init[ent][0]) == str:
                                init_path[entity] = reasoning_path_LLM_init[entity]
                            else:
                                init_path[entity] = reasoning_path_LLM_init[entity][0]
                        else:
                            if type(reasoning_path_LLM_init[entity]) == str:
                                init_path[entity] = reasoning_path_LLM_init[entity]
                            else:
                                init_path[entity] = reasoning_path_LLM_init[entity][0]
                    else:
                        if path is False:
                            for ent in reasoning_path_LLM_init.keys():
                                if type(reasoning_path_LLM_init[ent][0]) == str:
                                    init_path[ent] = reasoning_path_LLM_init[ent]
                                else:
                                    init_path[ent] = reasoning_path_LLM_init[ent][0]
                        else:
                            for ent in reasoning_path_LLM_init.keys():
                                if type(reasoning_path_LLM_init[ent]) == str:
                                    init_path[ent] = reasoning_path_LLM_init[ent]
                                else:
                                    init_path[ent] = reasoning_path_LLM_init[ent][0]


                    grounded_know = []
                   # 已有的知识, 其他topic的路径
                    if len(reasoning_paths)>0:
                        for know in reasoning_paths:
                            grounded_know.append(know)
                    # 已有的知识,当前路径
                    for know in grounded_knowledge_current:
                        grounded_know.append(know[1])


                    grounded_know_string = ""
                    for know in grounded_know:
                        if know == []:
                            continue
                        grounded_know_string+=utils.path_to_string(know) + "\n"

                    prompts = refine_prompt_path_one_path_1222  + "\nQuestion: " + question + "\nInitial Path:" + str(init_path) + "\nGrounded Knowledge:" + grounded_know_string +"\nCandidate Relations:" + str(ungrounded_neighbor_relation_dict) + "\nThought:"

                    while True:
                        response = self.run_llm(prompts, temperature=0.4, max_tokens=4096, opeani_api_keys="")
                        try:
                            new_reasoning_path_LLM_init=eval(response.split("Refined Path:")[-1].strip())
                            if type(new_reasoning_path_LLM_init) != dict:
                                raise ValueError("GPT generate type no match, regenerate")

                            if len(new_reasoning_path_LLM_init.keys()) == 0:
                                raise ValueError("GPT generate topics entities no match, regenerate")

                            if not path:
                                for k, v in new_reasoning_path_LLM_init.items():
                                    if type(v) != list:
                                        raise ValueError("GPT generate format no match, regenerate")
                            refine_time += 1
                            if one_path is True:
                                for key in new_reasoning_path_LLM_init.keys():
                                    if reasoning_path_LLM_init[key] == new_reasoning_path_LLM_init[key]:
                                        refine_time += 10
                                        print(response)
                                        print("****************************************************************************************")
                                    reasoning_path_LLM_init[key]=new_reasoning_path_LLM_init[key]
                            else:
                                reasoning_path_LLM_init = new_reasoning_path_LLM_init

                            break
                        except:
                            print(prompts)
                            print(response)
                            time.sleep(5)
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])

        return reasoning_paths, lists_of_paths



    def process_input(self, question_dict):
        '''
        Take question as input and return the input with prompt
        '''
        question = question_dict['question']

        if not question.endswith('?'):
            question += '?'

        if self.add_rule:
            graph = utils.build_graph(question_dict['graph'])
            entities = question_dict['q_entity']
            if self.use_true:
                rules = question_dict['ground_paths']
            elif self.use_random:
                _, rules = utils.get_random_paths(entities, graph)
            else:
                rules = question_dict['predicted_paths']
            if len(rules) > 0:
                reasoning_paths = self.apply_rules(graph, rules, entities)
                lists_of_paths = [utils.path_to_string(p) for p in reasoning_paths]
                # context = "\n".join([utils.path_to_string(p) for p in reasoning_paths])
            else:
                lists_of_paths = []
            #input += self.GRAPH_CONTEXT.format(context = context)

        input = self.QUESTION.format(question = question)
        # MCQ
        if len(question_dict['choices']) > 0:
            choices = '\n'.join(question_dict['choices'])
            input += self.CHOICES.format(choices = choices)
            if self.add_rule:
                instruction = self.MCQ_RULE_INSTRUCTION
            else:
                instruction = self.MCQ_INSTRUCTION
        # SAQ
        else:
            if self.add_rule:
                instruction = self.SAQ_RULE_INSTRUCTION
            else:
                instruction = self.SAQ_INSTRUCTION

        if self.cot:
            instruction += self.COT

        if self.explain:
            instruction += self.EXPLAIN

        if self.each_line:
            instruction += self.EACH_LINE

        if self.add_rule:
            other_prompt = self.prompt_template.format(instruction = instruction, input = self.GRAPH_CONTEXT.format(context = "") + input)
            context = self.check_prompt_length(other_prompt, lists_of_paths, self.maximun_token)

            input = self.GRAPH_CONTEXT.format(context = context) + input

        input = self.prompt_template.format(instruction = instruction, input = input)

        return input


    def check_prompt_length(self, prompt, list_of_paths, maximun_token):
        '''Check whether the input prompt is too long. If it is too long, remove the first path and check again.'''
        all_paths = "\n".join(list_of_paths)
        all_tokens = prompt + all_paths
        if self.tokenize(all_tokens) < maximun_token:
            return all_paths
        else:
            # Shuffle the paths
            random.shuffle(list_of_paths)
            new_list_of_paths = []
            # check the length of the prompt
            for p in list_of_paths:
                tmp_all_paths = "\n".join(new_list_of_paths + [p])
                tmp_all_tokens = prompt + tmp_all_paths
                if self.tokenize(tmp_all_tokens) > maximun_token:
                    return "\n".join(new_list_of_paths)
                new_list_of_paths.append(p)

"xxxxx"
# elif fun.startswith("trim_relation(") and fun.endswith(")"):
#     fun = fun.replace("trim_relation(","").replace(")", "").strip()
#     relation = fun.strip().strip("\'").strip("\"").strip()
#     start_index = new_path.find("-> "+relation)
#     if start_index==-1:
#         start_index = new_path.find("->"+relation)
#         if start_index==-1:
#             print("bad function call")
#             print(functions)
#             raise ValueError("bad function call")
#     new_path = new_path[:start_index].strip()
import os
import utils
from utils import *
from config import *
from pyserini.search import FaissSearcher, LuceneSearcher
from pyserini.search.hybrid import HybridSearcher
from pyserini.search.faiss import AutoQueryEncoder
from collections import deque

# load hybried searcher for relation binding
query_encoder = AutoQueryEncoder(encoder_dir='facebook/contriever', pooling='mean')
corpus = LuceneSearcher(os.path.join(CONTRIEVER_PATH, "contriever_fb_relation/index_relation_fb"))
bm25_searcher = LuceneSearcher(os.path.join(CONTRIEVER_PATH, 'contriever_fb_relation/index_relation_fb'))
contriever_searcher = FaissSearcher(os.path.join(CONTRIEVER_PATH, 'contriever_fb_relation/freebase_contriever_index'), query_encoder)
hsearcher = HybridSearcher(contriever_searcher, bm25_searcher)

def similar_relation_from_question(question, topk=5):
    """search similar relations according to the question. Aims for corrputed reasoning path.

    Args:
        question
        topk (Defaults to 5).

    Returns:
        retrieved relations
    """
    result = []
    hits = hsearcher.search(question, k=1000)[:topk]
    for hit in hits:
        result.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])
    return result

def grounding_relations(relation, topk=5):
    """bind a natural language relation to KG relation candidates

    Args:
        relation (_type_): _description_
        topk (int, optional): _description_. Defaults to 5.

    Returns:
        _type_: _description_
    """
    result_no_q = []
    relation_tokens = relation.replace("."," ").replace("_", " ").strip()
    hits = hsearcher.search(relation_tokens.replace("  "," ").strip(), k=1000)[:topk]
    for hit in hits:
        result_no_q.append(json.loads(corpus.doc(str(hit.docid)).raw())['rel_ori'])

    return result_no_q

def relation_binding(reasoning_path_LLM_init, topk=5):
    """bind all relations in the reasoning path to KG relation candidates

    Args:
        reasoning_path_LLM_init (dict): generated reasoning path from each topic entity
        topk (int, optional): bind a relation to topk candidates. Defaults to 5.

    Returns:
        grounded_relations (dict): grounded relations for each reasoning path
    """
    predicted_reasoning_path = []
    for keys in reasoning_path_LLM_init.keys():
        if type(reasoning_path_LLM_init[keys]) == str:
            predicted_reasoning_path.append(utils.string_to_path(reasoning_path_LLM_init[keys]))
        elif len(reasoning_path_LLM_init[keys])>0:
            predicted_reasoning_path.append(utils.string_to_path(reasoning_path_LLM_init[keys][0]))
                
    # bind all relations to KG relation candidates（faiss）
    grounded_relations = {}
    for r in predicted_reasoning_path:
        for rel in r:
            relations_no_q = grounding_relations(rel, topk=topk)
            if rel not in grounded_relations.keys():
                grounded_relations[rel] = relations_no_q
            else:
                grounded_relations[rel] = list(set(grounded_relations[rel]+relations_no_q))

    return grounded_relations


def bfs_for_each_path(entity_id, target_path, grounded_reasoning_set, options, max_que = 300):
    """
    Path connecting for each reasoning path, according to the reasoning path.
    This is essentially a BFS search for each relation in the reasoning path. Each layer of BFS search consists of candidate relations.
    In each layer, we check if neighbors of the current node have intersection with the candidate relation. If so, current relation is successfully instantiated.

    We return useful structured information (including currently instantiated instances and possible candidate relations in the failed points) for editing if instantiation fails.
    Args:
        entity_id : topic entity id for current reasoning path
        target_path : current reasoning path
        grounded_reasoning_set (list): list of grounded relation candidates for each position in the reasoning path
        options : parsed arguments
        max_que (int, optional): maximum queue size for each layer. Defaults to 300.

    Returns:
        result_paths : instantiated reasoning path (empty if instantiation fails)
        grounded_knowledge_current : stores all instances during BFS (length starting from 0)
        ungrounded_neighbor_relation_dict : if instantiation fails, store some relations as candidates for editing
    """
    result_paths = []
    current_position = 0
    queue = deque([(entity_id, [], current_position)])  # BFS queue. Container for entities, path instances and current position on path
    grounded_knowledge_current = []
    ungrounded_neighbor_relation_dict = {}

    while queue:
        size = len(queue)
        ungrounded_neighbor_relation_dict.clear()

        if options.verbose:
            print("current layer size when BFS", size)

        while size > 0:
            size -= 1
            current_node, current_path, current_position = queue.popleft()

            # push current grounded path to grounded_knowledge_current.
            # Note that grounded_knowledge_current stores all instantiated path (including length from 0 to current path length
            grounded_knowledge_current.append((current_node, current_path, current_position))

            if current_position == len(target_path) and current_path not in result_paths and len(current_path) > 0:
                result_paths.append(current_path)

            # continue instantiation if current path is shorter than predicted target_path
            if current_position < len(target_path):
                # get edges (relations) around current node (except previous relations)
                pre_relations = [rel[1] for rel in current_path]
                edge_set = utils.get_ent_one_hop_rel(current_node, pre_relations=pre_relations)
                if len(edge_set) == 0:
                    continue

                # take intersection
                list1 = grounded_reasoning_set[current_position]  # grounded relations for current position
                list2 = edge_set                                  # relations around current node
                list3 = pre_relations

                intersection_grounded = list(set(list1) & set(list2))    
                intersection_have_grounded = list(set(intersection_grounded) & set(list3))    
                intersection = list(set(intersection_grounded) - set(intersection_have_grounded))

                # no intersection for current node (something goes wrong), store some relations as candidates for editing
                if len(intersection) <= 0:
                    ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(current_node)] = edge_set
                    continue
                # grounded success. add to queue for next loop
                else:
                    for relation in intersection:
                        if len(queue) >= max_que:
                            break
                        # forward and backward relations
                        neighbors_with_relation = [neighbor for neighbor in utils.entity_search(current_node, relation, True) + utils.entity_search(current_node, relation, False)]
                        for neighbor in neighbors_with_relation:
                            if len(queue) < max_que:
                                queue.append((neighbor, current_path + [(utils.id2entity_name_or_type_en(current_node), relation, utils.id2entity_name_or_type_en(neighbor))], current_position + 1))
                            else:
                                break
                            
        if len(ungrounded_neighbor_relation_dict.keys()) == 0 and len(grounded_knowledge_current) == 1 and grounded_knowledge_current[-1][-1] == 0:
            ungrounded_neighbor_relation_dict[utils.id2entity_name_or_type_en(grounded_knowledge_current[-1][0])] = utils.get_ent_one_hop_rel(grounded_knowledge_current[-1][0])

    return result_paths, grounded_knowledge_current, ungrounded_neighbor_relation_dict
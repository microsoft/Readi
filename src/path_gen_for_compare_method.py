import sys, os
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/..")
from utils.freebase_func import *
from utils import readjson, savejson, jsonl_to_json, read_jsonl, id2entity_name_or_type_en
from tqdm import tqdm
import pickle
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import plotly.graph_objects as go
from scipy.stats import gaussian_kde


def sr_path_generation(intput_file, entity_file, golden_file):
    data = read_jsonl(intput_file)
    # entities = readlines(entity_file)
    with open(entity_file, 'rb') as file:
        entity_id2index = pickle.load(file)
    entity_index2id={}

    golden_data = readjson(golden_file)

    for key in entity_id2index.keys():
        entity_index2id[entity_id2index[key]] = key

    for index, line in enumerate(tqdm(data)) :
        paths = line['paths']
        path_string_list = []
        for p in paths:
            path_str_start = id2entity_name_or_type_en(entity_index2id[int(p[0])])
            if "END OF HOP" in p[1]:
                path_llm = path_str_start + " -> " + " -> ".join(p[1][:-1])
            else:
                path_llm = path_str_start + " -> " + " -> ".join(p[1])
            # print(path_llm)
            path_string_list.append(path_llm)
        line['path_string_list'] = path_string_list
        line['answer'] = golden_data[index]['answer']
        del line['subgraph']
        del line['paths']
        del line['answers']

    savejson("/home/v-sitaocheng/demos/dangle_over_ground/data/compare_model_path/cwq_sr_path.json", data)


def rog_path_generation(intput_file,golden_file):
    data = read_jsonl(intput_file)
    # entities = readlines(entity_file)
    golden_data = readjson(golden_file)

    for index, line in enumerate(tqdm(data)):
        paths = line['prediction']
        entities = [v for k, v in golden_data[index]['topic_entity'].items()]
        path_string_list = []

        for p in paths:
            for path_str_start in entities:
                path_llm = path_str_start + " -> " + " -> ".join(p)
                path_string_list.append(path_llm)

        line['path_string_list'] = path_string_list
        del line['raw_output']
        line['answer'] = golden_data[index]['answer']
        line['topic_entity'] = golden_data[index]['topic_entity']
    savejson("/home/v-sitaocheng/demos/dangle_over_ground/data/compare_model_path/cwq_rog_path.json", data)


def path_merging_with_beam_size(beam_size):
    file_1 = read_jsonl("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_campre_method___compare_sr_beam1_0114.jsonl")[:1000]
    file_2 = read_jsonl("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_campre_method___compare_sr_beam2_0115.jsonl")
    # file_3 = read_jsonl("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_campre_method___compare_rog_beam3_0115.jsonl")

    file_beam_assambled = []
    for index, line in enumerate(tqdm(file_1)):
        cur_kg_triples_str = list(set(line['kg_triples_str'].split("\n")))
        cur_kg_triples_str += list(set(file_2[index]['kg_triples_str'].split("\n")))
        # cur_kg_triples_str += list(set(file_3[index]['kg_triples_str'].split("\n")))
        cur_kg_triples_str = list(set(cur_kg_triples_str))
        
        line['kg_triples_str'] = "\n".join(cur_kg_triples_str)

    savejson("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_campre_method___compare_sr_beam2_assembled.json", file_1)


def print_graph_2plots():
    # # 创建数据
    # data = {
    #     'Beam': [1, 2, 3],
    #     'SR AnswerCoverage': [0.475, 0.582, 0.583],
    #     'RoG AnswerCoverage': [0.508, 0.657, 0.73],
    #     'SR One-path ac': [0.442, 0.550, 0.546],
    #     'RoG One-path ac': [0.512, 0.606, 0.661],
    #     'SR Multi-path ac': [0.518, 0.631, 0.631],
    #     'RoG Multi-path ac': [0.502, 0.724, 0.818]
    # }

    # 数据

    top_k_relation_paths = np.array([1, 2, 3 ])
    retrieved_reasoning_paths_rog = np.array([69.51, 129.59, 170.01])
    retrieved_reasoning_paths_sr = np.array([26.25, 47.15, 47.15])  # 新增的数据
    retrieved_reasoning_paths_ours = np.array([93.73, 93.73, 93.73])  # 新增的数据

    answer_coverage_rog = np.array([50.8, 65.7, 73.0])
    answer_coverage_sr = np.array([47.5, 58.2, 58.3])
    answer_coverage_ours = np.array([54.4, 54.4, 54.4])

    qa_rog = np.array([53.1, 54.7, 56.0])
    qa_sr = np.array([51.8, 53.9, 52.3])  # 新增的数据
    qa_ours = np.array([56.9, 56.9, 56.9])  # 新增的数据

    acrr_rog = np.array([50.8**2/69.51, 65.7**2/129.59, 73.0**2/170.01])
    acrr_sr = np.array([47.5**2/26.25, 58.2**2/47.15, 58.3**2/47.15])
    acrr_ours = np.array([54.4**2/97.73, 54.4**2/93.73, 54.4**2/93.73])
    # fig, ax1 = plt.subplots()
    fig, axs = plt.subplots(1, 2, figsize=(10, 10))  # 创建两个子图

    # 柱状图
    width = 0.2  # 柱子的宽度

    rects1 = axs[0].bar(top_k_relation_paths - width, retrieved_reasoning_paths_sr, width, color='lightgreen', label='# Retrieved Triples of SR')
    rects2 = axs[0].bar(top_k_relation_paths, retrieved_reasoning_paths_rog, width, color='lightgray', label='# Retrieved Triples of RoG')  # 新增的柱子
    rects3 = axs[0].bar(top_k_relation_paths + width, retrieved_reasoning_paths_ours, width, color='skyblue', label='# Retrieved Triples of Ours')  # 新增的柱子

    # ax1.legend(fontsize=8)  # 显示图例
    axs[0].set_xlabel('beam size of fine-tuned models')
    axs[0].set_ylabel('# Retrieved Knowledge',  fontsize=14)
    axs[0].set_xticks([1, 2, 3])  # x轴显示1，2，3

    # 折线图
    ax2 = axs[0].twinx()
    line1, = ax2.plot(top_k_relation_paths, answer_coverage_rog, 'r-', marker='*',  markersize=5, label='Answer Coverage(%) of RoG')
    line2, = ax2.plot(top_k_relation_paths, answer_coverage_sr, 'm-', marker='o', markersize=5,  label='Answer Coverage(%) of SR')
    line3, = ax2.plot(top_k_relation_paths, answer_coverage_ours, 'b-', markersize=5,  label='Answer Coverage(%) of Ours')
    ax2.set_ylabel('Answer Coverage (%)',  fontsize=14)
    # ax2.legend(loc='upper right',fontsize=8)


    rects4 = axs[1].bar(top_k_relation_paths - width, qa_rog, width, color='lightgreen', label='# Retrieved Triples of SR')
    rects5 = axs[1].bar(top_k_relation_paths, qa_sr, width, color='lightgray', label='# Retrieved Triples of RoG')  # 新增的柱子
    rects6 = axs[1].bar(top_k_relation_paths + width, qa_ours, width, color='skyblue', label='# Retrieved Triples of Ours')  # 新增的柱子

    # ax1.legend(fontsize=8)  # 显示图例
    axs[1].set_xlabel('beam size')
    axs[1].set_ylabel('QA performance (Hit@1)',  fontsize=14)
    axs[1].set_xticks([1, 2, 3])  # x轴显示1，2，3

    # 折线图
    ax2 = axs[1].twinx()
    line1, = ax2.plot(top_k_relation_paths, acrr_rog, 'r-', marker='*',  markersize=5, label='Answer Coverage(%) of RoG')
    line2, = ax2.plot(top_k_relation_paths, acrr_sr, 'm-', marker='o', markersize=5,  label='Answer Coverage(%) of SR')
    line3, = ax2.plot(top_k_relation_paths, acrr_ours, 'b-',  markersize=5, label='Answer Coverage(%) of Ours')
    ax2.set_ylabel('Answer Coverage (%) / # Retrieved Knowledge',  fontsize=14)

    # 图例
    lines = [rects1,line1, rects2, line2, rects3,   line3]
    labels = [l.get_label() for l in lines]

        
    plt.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.5, 1.15), fancybox=True, shadow=True, ncol=3, fontsize='small')  # 图例在图的上方
    plt.suptitle("Quality of retrieved knowledge on CWQ 1000 samples", fontsize=16, y=0.98) 
    plt.tight_layout()
    plt.savefig("./ac_hit_compare.png")

def print_graph_1plot():
    top_k_relation_paths = np.arange(3)
    retrieved_reasoning_paths_rog = np.array([69.51, 129.59, 170.01])
    retrieved_reasoning_paths_sr = np.array([26.25, 47.15, 47.15])  # 新增的数据
    retrieved_reasoning_paths_ours = np.array([93.73, 93.73, 93.73])  # 新增的数据
    retrieved_reasoning_paths_init = np.array([134.85, 134.85, 134.85])  # 新增的数据

    answer_coverage_rog = np.array([50.8, 65.7, 73.0])
    answer_coverage_sr = np.array([47.5, 58.2, 58.3])
    answer_coverage_ours = np.array([54.4, 54.4, 54.4])
    answer_coverage_init = np.array([47.2, 47.2, 47.2])

    qa_rog = np.array([53.1, 54.7, 56.0])
    qa_sr = np.array([51.8, 53.9, 52.3])  # 新增的数据
    qa_ours = np.array([56.9, 56.9, 56.9])  # 新增的数据

    fig, ax1 = plt.subplots()

    # 柱状图
    width = 0.1  # 柱子的宽度

    rects1 = ax1.bar(top_k_relation_paths - 2*width, retrieved_reasoning_paths_sr, width, color='skyblue', label='# RK of SR')
    rects2 = ax1.bar(top_k_relation_paths - width, retrieved_reasoning_paths_rog, width, color='#D8BFD8', label='# RK of RoG')  # 新增的柱子
    rects3 = ax1.bar(top_k_relation_paths , retrieved_reasoning_paths_init, width, color='#FFDAB9', label='# RK Our init path')  # 新增的柱子
    rects4 = ax1.bar(top_k_relation_paths + width, retrieved_reasoning_paths_ours, width, color='#FF7F7F', label='# RK of Our edited path')  # 新增的柱子

    # ax1.legend(fontsize=8)  # 显示图例
    ax1.set_xlabel('beam size of fine-tuned model')
    ax1.set_ylabel('# Retrieved Knowledge',  fontsize=14)
    ax1.set_xticks([0, 1, 2])  # x轴显示1，2，3
    ax1.set_xticklabels(['1','2','3'])

    # 折线图
    ax2 = ax1.twinx()
    line1, = ax2.plot(top_k_relation_paths, answer_coverage_sr, 'darkblue', marker='o', markersize=5,  label='AC(%) of SR')
    line2, = ax2.plot(top_k_relation_paths, answer_coverage_rog, 'purple', marker='*',  markersize=5, label='AC(%) of RoG')
    line3, = ax2.plot(top_k_relation_paths, answer_coverage_init, 'red', markersize=5,  label='AC(%) of Our init path')
    line4, = ax2.plot(top_k_relation_paths, answer_coverage_ours, 'darkred', markersize=5,  label='AC(%) of Our edited path')
    ax2.set_ylabel('Answer Coverage (%)',  fontsize=14)
    # # 新增的虚线折线图
    # line4, = ax2.plot(top_k_relation_paths, qa_sr, 'm--', marker='o', markersize=5,  label='QA(%) of SR')
    # line5, = ax2.plot(top_k_relation_paths, qa_rog, 'r--', marker='*',  markersize=5, label='QA(%) of RoG')
    # line6, = ax2.plot(top_k_relation_paths, qa_ours, 'b--', markersize=5,  label='QA(%) of Ours')

    # 图例
    lines = [rects1, line1, rects2, line2, rects3, line3, rects4, line4]
    labels = [l.get_label() for l in lines]

    plt.legend(lines, labels, loc='upper center', bbox_to_anchor=(0.50, 1.17), fancybox=True, shadow=True, ncol=4, fontsize='small')  # 图例在图的上方
    plt.suptitle("Quality of retrieved knowledge on CWQ 1000 samples", fontsize=16, y=0.93) 
    plt.tight_layout()

    plt.savefig("./ac_hit_compare.png")


def reliability_subgraph():
    # 设置图形大小
    plt.figure(figsize=(5, 4.3))
    # 创建子图
    ax = plt.subplot(111)
    # 设置x轴和y轴的标签
    ax.set_xlabel('Methods', fontsize=12)
    ax.set_ylabel('Length of Path (Len.)', fontsize=12)
    # 设置x轴的刻度和标签
    x = ['Golden Path', 'SR', 'RoG', 'Readi-init(gpt3.5)', "Readi-full(gpt3.5)"]
    xticks = range(len(x))
    ax.set_xticks(xticks)
    ax.set_xticklabels(x, rotation=15, fontsize=8)
    # 设置y轴的范围
    ax.set_ylim(0, 5)
    # 设置图形标题
    ax.set_title('Features of Reasoning Path')
    # 设置网格线
    ax.grid(True, linestyle='--', alpha=0.5)
    # 绘制柱状图，每个指标用一种颜色表示
    colors = ['red', 'green', 'blue', 'orange', 'purple']
    width = 0.15 # 柱子的宽度
    # LPP指标
    y1 = [3.2, 3.65, 2.55, 4.28, 3.37]
    rect1= ax.bar([i - width * 2 for i in xticks], y1, width=width, color=colors[0], label='Len. of Predict Path', alpha=0.7)
    # LIP指标
    y2 = [3.2, 3.28, 1.37, 2.54, 2.84]
    rect2 = ax.bar([i - width for i in xticks], y2, width=width, color=colors[1], label='Len. of Instantiate Path', alpha=0.3)


    ax2 = ax.twinx()
    ax2.set_ylabel('Quality of Instantiation (%)',  fontsize=12)
    ax2.set_ylim(0, 119)

    # AIP指标
    y3 = [100, 88, 55, 64, 86]
    rect3 = ax2.bar(xticks, y3, width=width, color=colors[2], label='Avg. Instantiate Prog(%)', alpha=0.75)
    # GSR指标
    y4 = [100, 86, 50, 46, 80]
    rect4 = ax2.bar([i + width for i in xticks], y4, width=width, color=colors[3], label='Instantiate Success(%)', alpha=0.75)
    # IER指标
    y5 = [0, 1, 2, 49, 22]
    rect5 = ax2.bar([i + width * 2 for i in xticks], y5, width=width, color=colors[4], label='Inter. Node Ending(%)', alpha=0.5)    # 显示图例
    # 在柱子上方显示数值
    # for i in range(len(x)):
        # # LPP数值
        # plt.text(i - width * 2, y1[i] + 0.05, '%.2f' % y1[i], ha='center', va='bottom')
        # # LIP数值
        # plt.text(i - width, y2[i] + 0.05, '%.2f' % y2[i], ha='center', va='bottom')
        # # AIP数值
        # plt.text(i, y3[i] + 0.05, '%.2f' % y3[i], ha='center', va='bottom')
        # GSR数值
        # plt.text(i + width, y4[i] + 0.11, '%.2f' % y4[i], ha='center', va='bottom')
        # IER数值
        # plt.text(i + width * 2, y5[i] + 0.01, '%.2f' % y5[i], ha='center', va='bottom', fontsize=6.5)
    
    # 图例
    lines = [rect1,rect2,rect3, rect4,rect5]
    labels = [l.get_label() for l in lines]

    # plt.legend(lines, labels, loc='upper left',  fancybox=True, shadow=True, ncol=2, fontsize=7)  # 图例在图的上方
   
    ax.legend(loc='upper left', ncol=1, fontsize=6)
    ax2.legend(loc='upper right', ncol=1, fontsize=6)
    ax2.hlines(y=100, xmin=-0.05, xmax=4.5,linestyles="dashed")
    ax.hlines(y=3.2, xmin=-0.3, xmax=4, linestyles="dashed")
    plt.tight_layout()
    plt.savefig("./reliability.png")


def scatter_graph():
    # 设置图形大小
    sns.set(rc={'figure.figsize':(10, 6)})
    # 创建子图
    ax = plt.subplot(111)
    # 设置x轴和y轴的标签
    ax.set_xlabel('Methods')
    ax.set_ylabel('Metrics of Path Quality')
    # 设置x轴的刻度和标签
    x = ['Golden Path', 'SR', 'RoG', 'Readi-init', "Readi-full"]
    xticks = range(len(x))
    ax.set_xticks(xticks)
    ax.set_xticklabels(x, rotation=30)
    # 设置y轴的范围
    ax.set_ylim(0, 5)
    # 设置图形标题
    ax.set_title('Reliability of Path by Different Methods')
    # 设置网格线
    ax.grid(True, linestyle='--', alpha=0.5)
    # 绘制散点图，每个指标用一种颜色表示，每个方法用一种形状表示
    colors = ['red', 'green', 'blue', 'orange', 'purple']
    markers = ['o', 's', '^', 'v', 'd']
    # LPP指标
    y1 = [3.2, 3.65, 2.55, 4.28, 4.37]
    sns.relplot(x=xticks, y=y1, hue=['LPP']*len(x), style=x, palette=colors, markers=markers, ax=ax, size=10)
    # LIP指标
    y2 = [3.2, 3.28, 1.37, 2.54, 2.84]
    sns.relplot(x=xticks, y=y2, hue=['LIP']*len(x), style=x, palette=colors, markers=markers, ax=ax, size=10)
    # AIP指标
    y3 = [1, 0.88, 0.55, 0.64, 0.86]
    sns.relplot(x=xticks, y=y3, hue=['AIP']*len(x), style=x, palette=colors, markers=markers, ax=ax, size=10)
    # GSR指标
    y4 = [1, 0.86, 0.5, 0.46, 0.8]
    sns.relplot(x=xticks, y=y4, hue=['GSR']*len(x), style=x, palette=colors, markers=markers, ax=ax, size=10)
    # IER指标
    y5 = [0, 0.01, 0.02, 0.49, 0.22]
    sns.relplot(x=xticks, y=y5, hue=['IER']*len(x), style=x, palette=colors, markers=markers, ax=ax, size=10)
    # 关闭多余的图形

    # 显示图形
    plt.tight_layout()
    plt.savefig("./scatter_plot.png")

def graph_radar():
    # # 设置图形大小
    # fig = go.Figure(layout=go.Layout(width=700, height=550))
    # # 设置图形标题
    # fig.update_layout(title='Relative Quality of Path of Different Methods with Golden')
    # # 设置极坐标的角度和标签
    # theta = ['Len. of Predict Path', 'Len. of Instantiate Path', 'Avg. Instantiate Progress', 'Grounding Success(%)', 'Ending with Inter. Node(%)']
    # # 设置极坐标的范围
    # rmax = 5
    # # 绘制雷达图，每个方法用一种颜色表示
    # colors = ['orange', 'lightgreen', 'purple', 'red', 'skyblue']
    # # Golden Path
    # # r1 = [3.2, 3.2, 1, 1, 0]
    # r1 = [1, 1, 1, 1, 1]
    # fig.add_trace(go.Scatterpolar(r=r1, theta=theta, fill='toself', name='Golden Path', line_color=colors[4]))
    # # SR
    # r2 = [1-(3.65-3.2)/3.2, 1-(3.28-3.2)/3.2, 0.88, 0.86, 1-0.01]
    # fig.add_trace(go.Scatterpolar(r=r2, theta=theta, fill='toself', name='SR', line_color=colors[1]))
    # # RoG
    # r3 = [1-(3.2-2.55)/3.2, 1-(3.2-1.37)/3.2, 0.55, 0.5, 1-0.02]
    # fig.add_trace(go.Scatterpolar(r=r3, theta=theta, fill='toself', name='RoG', line_color=colors[2]))
    # # ChatGPT3.5
    # r4 = [1-(4.28-3.2)/3.2, 1-(3.2-2.54)/3.2, 0.64, 0.46, 1-0.49]
    # fig.add_trace(go.Scatterpolar(r=r4, theta=theta, fill='toself', name='Readi-init(gpt3.5)', line_color=colors[3]))
    # # Edition
    # r5 = [1-(4.37-3.2)/3.2, 1-(3.2-2.84)/3.2, 0.86, 0.8, 1-0.22]
    # fig.add_trace(go.Scatterpolar(r=r5, theta=theta, fill='toself', name='Readi-full(gpt3.5)', line_color=colors[0]))
    # # 显示图形
    # fig.show()


    # 数据
    labels = np.array(['Len. of\nPredict Path', 'Len. of\nInstantiate Path', 'Avg. Instantiate Progress', 'Instantiate\nSuccess (%)', '1-Intermediate Node Ending(%)', 'QA Hit@1'])
    data = np.array([
        [1, 1, 1, 1, 1, 1],  # Golden Path
        [1-(3.65-3.2)/3.2, 1-(3.28-3.2)/3.2, 0.88, 0.86, 1-0.01, 0.518],  # SR (Zhang et al., 2022)
        [1-(3.2-2.55)/3.2, 1-(3.2-1.37)/3.2, 0.55, 0.5, 1-0.02, 0.531],  # RoG (Luo et al., 2023)
        [1-(4.28-3.2)/3.2, 1-(3.2-2.54)/3.2, 0.64, 0.46, 1-0.49, 0.502],  # ChatGPT3.5
        [1-(3.37-3.2)/3.2, 1-(3.2-2.84)/3.2, 0.86, 0.8, 1-0.22, 0.569]  # + Edition
    ])
    methods = ['Golden Path', 'SR', 'RoG', 'Readi-init(gpt3.5)', 'Readi-full(gpt3.5)']

    # 计算角度
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()

    # 使雷达图封闭
    data = np.concatenate((data, [data[0]]))
    angles += angles[:1]

    # 绘图
    fig, ax = plt.subplots(figsize=(7.5, 6.5), subplot_kw=dict(polar=True))
    for i in range(len(methods)):
        values = data[i]
        values = np.concatenate((values, [values[0]]))  # 使雷达图封闭
        ax.plot(angles, values, label=methods[i])
        ax.fill(angles, values, alpha=0.25)
    ax.set_yticklabels([])
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=14)  # 注意这里我们只使用前5个角度来设置标签
    plt.title('Features of Reasoning Path of Different Methods Relative to Golden', fontsize=15)
    plt.legend(bbox_to_anchor=(1.1, 0.17),title="Methods",loc='center right', ncol=1, fontsize=10,)
   
    plt.tight_layout()
    plt.savefig('./radar.png')

def call_me_distribution():
    count_dict = {0: 584, 2: 188, 5: 48, 7: 32, 3: 97, 1: 372, 4: 60, 6: 42}
    plt.figure(figsize=(3.8, 3))
    # 将字典转换为列表，列表中的每个元素是一个数字，这个数字在列表中出现的次数等于字典中这个数字对应的值
    data = [k for k, v in count_dict.items() for _ in range(v)]

    # 计算概率密度函数
    density = gaussian_kde(data)

    # 画出平滑的概率密度曲线
    x = np.linspace(min(data), max(data), 1000)
    plt.plot(x, density(x), label='Probability Density')

    # 用红色的点标出数据的均值
    mean_value = 1.40
    plt.plot(mean_value, density(mean_value), 'ro', label='Mean Value')

    # 添加图例
    plt.legend(fontsize=8)

    # 画出概率分布图
    plt.xlabel('LLM-Call Times')
    plt.ylabel('Density')
    plt.title('Distribution of Edition LLM-Call Times')
    plt.tight_layout()
    plt.savefig("./efficient_distribution.png")

def call_me_bar():
    count_dict = {0: 584, 2: 188, 5: 48, 7: 32, 3: 97, 1: 372, 4: 60, 6: 42}
    plt.figure(figsize=(4, 3))

    # 计算总的次数
    total_count = sum(count_dict.values())

    # 创建一个新的字典，键是数字，值是这些数字出现的概率
    prob_dict = {k: v / total_count for k, v in count_dict.items()}

    # 画出概率分布图
    plt.bar(prob_dict.keys(), prob_dict.values(), alpha=0.5)
    # 添加图例
    # plt.legend(fontsize=8)

    # 画出概率分布图
    plt.xlabel('LLM-Call Times')
    plt.ylabel('Frequent Density')
    plt.title('Distribution of Edition LLM-Call Times')
    plt.tight_layout()
    plt.savefig("./efficient_bar.png")


def dedup_json(input_file):
    import json
    import jsonlines

    if input_file.endswith("json"):
        with open(input_file, "r") as f:
            data = json.load(f)
    else:
        with jsonlines.open(input_file, "r") as f:
            data = list(f)

    # 创建一个空的列表，用来存储去重后的问题
    unique_questions = []

    # 创建一个空的集合，用来记录已经出现过的问题
    seen_questions = set()

    # 遍历 json 字典中的每一项
    for item in data:
        # 获取当前项的 "question" 字段的值
        question = item["question"]
        # 如果这个问题没有出现过
        if question not in seen_questions:
            # 将这个问题添加到集合中，表示已经出现过
            seen_questions.add(question)
            # 将这个问题添加到列表中，表示保留
            unique_questions.append(item)

    # 打开一个新的 json 文件，写入去重后的数据
    if input_file.endswith("json"):
        with open(input_file.split(".")[0]+"_dedup.json", "w") as f:
            json.dump(unique_questions, f, indent=4)
    else:
        with jsonlines.open(input_file.split(".")[0]+"_dedup.jsonl", "w") as f:
            f.write_all(unique_questions)


    # 打印去重后的问题的数量
    print(f"去重后的问题有 {len(unique_questions)} 个")

# input_file="/home/v-sitaocheng/demos/llm_hallu/subgraph_retrieval/sr_cwq/SubgraphRetrievalKBQA/debug/cwq_retrieved_graph_cache/data/cwq/SubgraphRetrievalKBQA/src/tmp/reader_data/CWQ/test_simple.json"
# entity_file = '/home/v-sitaocheng/demos/llm_hallu/subgraph_retrieval/sr_cwq/SubgraphRetrievalKBQA/debug/ent2id.pickle'
# golden_file = "/home/v-sitaocheng/demos/dangle_over_ground/data/datasets/cwq_test.json"

# sr_path_generation(input_file, entity_file, golden_file)

# input_file="/home/v-sitaocheng/demos/reasoning-on-graphs/results/gen_rule_path/RoG-cwq/RoG/test/predictions_3_False.jsonl"
# golden_file = "/home/v-sitaocheng/demos/dangle_over_ground/data/datasets/cwq_test.json"
# rog_path_generation(input_file, golden_file)

# path_merging_with_beam_size(3)

# scatter_graph()
# graph_radar()
# reliability_subgraph()
# call_me_distribution()
# call_me_bar()


dedup_json("/home/v-sitaocheng/demos/dangle_over_ground/results/KGQA/cwq/cwq_gpt35_llm_refine_sequence_err_msg_final_0119.jsonl")
import functools
import json
import math
import os
import random

import jinja2

from hive_map import MAP

NUM_FREQS = 52
SCALE_FACTOR = 73
ADD_X = 50
ADD_Y = 100


def render_grid_html(nodes):
    return jinja2.Template("""
        <style>
        .node {
            position: absolute;
            width: 120px;
            height: 120px;
            border: 1px solid #ccc;
            border-radius: 50%;
            text-align: center;
            vertical-align: middle;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        </style>
        {% for node in nodes %}
        <div class="node" style="left: {{ xpos(node) }}px; top: {{ ypos(node) }}px;">
            {{ node["freq"][0] }},{{ node["freq"][1] }}
        </div>
        {% endfor %}
    """).render(
        nodes=nodes,
        xpos=lambda node: node["x"] * SCALE_FACTOR + ADD_X,
        ypos=lambda node: node["y"] * SCALE_FACTOR / 2 + ADD_Y
    )


def copy_nodes(nodes):
    return [dict(node) for node in nodes]


def preview_grid(nodes, out_file="./out/grid.html"):
    open(out_file, "w").write(render_grid_html(nodes=nodes))


def node_distance(node_a, node_b):
    return math.sqrt((node_a["x"] - node_b["x"]) ** 2 + (node_a["y"] - node_b["y"]) ** 2)


def calc_neighbors(nodes, distance):
    nodes.sort(key=lambda node: node["id"])
    for node_a in nodes:
        for node_b in nodes:
            if node_a["id"] == node_b["id"]:
                continue
            if node_distance(node_a, node_b) <= distance:
                node_a["near"].append(node_b["id"])


def find_node(cur_node_id, nodes):
    for node in nodes:
        if node["id"] == cur_node_id:
            return node


def get_all_freqs():
    return {i for i in xrange(1, NUM_FREQS + 1)}


def one_freq_get_possible_freqs_for_node(node, nodes):
    ret = get_all_freqs()

    for near_id in node["near"]:
        near_freq = find_node(near_id, nodes).get("freq")
        if near_freq is None:
            continue
        ret -= {near_freq}
        #ret -= {i for i in xrange(near_freq - 2, near_freq + 3)}

    return ret


def one_freq_pick_alg(cur_node, nodes):
    l = list(one_freq_get_possible_freqs_for_node(cur_node, nodes))
    random.shuffle(l)
    return l


def two_freq_var1_get_possible_freqs_for_node(node, nodes):
    free_freqs = get_all_freqs()

    for near_id in node["near"]:
        near_freqs = find_node(near_id, nodes).get("freq")
        if near_freqs is None:
            continue
        free_freqs -= {i for i in xrange(near_freqs[0] - 2, near_freqs[0] + 3)}
        free_freqs -= {i for i in xrange(near_freqs[1] - 2, near_freqs[1] + 3)}

    for freq1 in free_freqs:
        for freq2 in free_freqs:
            if abs(freq1 - freq2) < 30:
                continue
            if freq1 > freq2:
                continue
            yield freq1, freq2


def two_freq_var1_pick_alg(cur_node, nodes):
    l = list(two_freq_var1_get_possible_freqs_for_node(cur_node, nodes))
    copy = copy_nodes(nodes)
    cur_copy = find_node(cur_node["id"], copy)

    def score_for_suggestion(freqs):
        cur_copy["freq"] = freqs
        score = two_freq_calc_score(copy)
        return score

    random.shuffle(l)
    l.sort(key=score_for_suggestion)
    return l


def backtrack_freqs_abstract(nodes, cur_node_id=1, pick_alg=None):
    nodes = copy_nodes(nodes)
    cur_node = find_node(cur_node_id, nodes)

    if cur_node is None:
        # We've finished everything!
        return nodes

    for pick in pick_alg(cur_node, nodes):
        cur_node["freq"] = pick
        ret = backtrack_freqs_abstract(nodes, cur_node_id + 1, pick_alg=pick_alg)
        if ret is not None:
            return ret

    return None

one_freq_backtrack = functools.partial(backtrack_freqs_abstract, pick_alg=one_freq_pick_alg)
two_freq_var1_backtrack = functools.partial(backtrack_freqs_abstract, pick_alg=two_freq_var1_pick_alg)


def two_freq_calc_score(nodes):
    all_freqs = {node["freq"][0] for node in nodes if "freq" in node} | {node["freq"][1] for node in nodes if "freq" in node}

    score = 0.0
    for freq in all_freqs:
        freq_nodes = [node for node in nodes if "freq" in node and freq in node["freq"]]
        for node1 in freq_nodes:
            for node2 in freq_nodes:
                if node1 == node2:
                    continue
                score += 1.0 / node_distance(node1, node2)
    return score


def main():
    winner = None
    winner_score = -1

    for i in xrange(100):
        if (i % 10 == 0):
            print i
        nodes = copy_nodes(two_freq_var1_backtrack(MAP))
        cur_score = two_freq_calc_score(nodes)
        if winner_score == -1 or cur_score < winner_score:
            print "---->", cur_score
            winner_score = cur_score
            winner = nodes

    try:
        os.mkdir("./out")
    except:
        pass

    open("./out/winner.json", "w").write(json.dumps(winner, indent=4))
    print "---->", two_freq_calc_score(winner)
    preview_grid(winner)


if __name__ == "__main__":
    main()
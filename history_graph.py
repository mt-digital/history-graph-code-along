'''
Class for working with the COGS 202 history graph of famous cognitive
scientists.

Author: Matthew Turner <maturner01@gmail.com>
Date: February 7, 2016
'''

import json
import matplotlib.pyplot as plt
import networkx as nx
import os
import shutil
import warnings

from numpy import array
from pandas import DataFrame
from subprocess import call


plt.style.use('ggplot')


YOSHIMI_GITHUB_REPO = 'https://github.com/jyoshimi/history_graph'


class HistoryGraph:

    def __init__(self, github_repo=YOSHIMI_GITHUB_REPO,
                 git_clone_dir='history_graph_repo'):

        if os.path.isdir(git_clone_dir):
            shutil.rmtree(git_clone_dir)

        p = call(['git', 'clone', github_repo, git_clone_dir])

        # load history graph from history_graph.js
        # we use os.path.join so it's platform-independent (OS X, Windows, etc)
        os.chdir(git_clone_dir)
        self.history_graph_path = os.path.join('history_net_data.js')

        self.history_graph = _load_history_graph(self.history_graph_path)

        self.networkx_history_graph = _make_nx_graph(self.history_graph)

    def barplot_most_connected(self, **mpl_kwargs):

        g = self.networkx_history_graph

        degrees = list(g.degree().items())
        degrees.sort(key=lambda x: x[1])

        names = [a[0] for a in degrees]
        k = [a[1] for a in degrees]

        df = DataFrame(index=names, data=k)
        df.plot(kind='barh', **mpl_kwargs)

        plt.title('Connections per cognitive scientist')

    def refresh_networkx_history_graph(self):

        self.networkx_history_graph = _make_nx_graph(self.history_graph)

    def visualize(self, **kwargs):

        self.refresh_networkx_history_graph()

        nxhg = self.networkx_history_graph

        _vis_graph(nxhg, **kwargs)

    def sync_history_graph(self, commit_message):

        _write_history_graph(self.history_graph, self.history_graph_path)

        p = Popen(['git', 'add', self.history_graph_path])
        if p.returncode > 0:
            raise RuntimeError(
                'adding history graph failed! Error message:\n{}'.format(
                    p.communicate()
                )
            )

        p = Popen(['git', 'commit', '-m', commit_message])
        if p.returncode > 0:
            raise RuntimeError(
                'Commit failed! Error message:\n{}'.format(
                    p.communicate()
                )
            )

        p = Popen(['git', 'push', 'origin', 'master'])
        if p.returncode > 0:
            raise RuntimeError(
                'Push to github failed! Error message:\n{}'.format(
                    p.communicate()
                )
            )


def _load_history_graph(history_graph_path):

    hg_raw = open(history_graph_path, 'r').read()

    hg_proc = hg_raw.replace('data = ', '')

    data = json.loads(hg_proc)

    return data


def _write_history_graph(history_graph, history_graph_path):

    s = json.dumps(history_graph)
    s = 'data = ' + s

    open(history_graph_path, 'w').write(s)


def _make_nx_graph(json_history_graph):

    edges = json_history_graph['edges']
    edges_proc = [(edge['from'].title(), edge['to'].title()) for edge in edges]

    nodes = json_history_graph['nodes']
    nodes_proc = [node['label'] for node in nodes]

    nodes_with_edge = [e[0] for e in edges_proc] + [e[1] for e in edges_proc]

    disconnected_nodes = [
        node for node in nodes_proc if node not in nodes_with_edge
    ]

    g = nx.Graph(edges_proc)
    # g.add_nodes_from(disconnected_nodes)

    return g


def _vis_graph(g, node_color='r', figsize=(10, 10),
               layout='graphviz', alpha=0.5,
               labels_x_offset=0.1, labels_y_offset=0.1):

    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111)

    if layout == 'graphviz':
        node_pos = nx.drawing.nx_pydot.graphviz_layout(g)
    elif layout == 'circular':
        node_pos = nx.drawing.layout.circular_layout(g)
    elif layout == 'spectral':
        node_pos = nx.drawing.layout.spectral_layout(g)
    elif layout == 'spring':
        node_pos = nx.drawing.layout.spring_layout(g)
    elif layout == 'shell':
        node_pos = nx.drawing.layout.shell_layout(g)
    else:
        warnings.warn(
            'layout {} not found, defaulting to graphviz'.format(layout)
        )
        node_pos = nx.drawing.nx_pydot.graphviz_layout(g)

    if node_pos not in ['spring']:
        label_pos = {
            k: array(
                [v[0] + labels_x_offset, v[1] + labels_y_offset]
            )
            for k, v in node_pos.items()
        }

    nx.draw_networkx_labels(g, font_weight='bold', font_size=18, pos=label_pos)
    nx.draw_networkx_nodes(g, node_size=500,
                           node_color=node_color, pos=node_pos, alpha=alpha)
    nx.draw_networkx_edges(g, pos=node_pos, edge_color='grey', width=1.0)

    return fig, ax

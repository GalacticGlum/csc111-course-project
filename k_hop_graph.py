"""A tool for visualising k-hop graphs.

NOTE: This is rough work, and not actually part of the final project. See the project report
for more details.
"""
import tqdm
import logging
import argparse
from pathlib import Path
from typing import Tuple, Set, Optional, Generator, Union

import numpy as np
import tikzplotlib
import networkx as nx
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import community as community_louvain
from matplotlib.collections import LineCollection

from fa2 import ForceAtlas2
from sklearn import metrics
from curved_edges import curved_edges

from logger import logger
from card_embeddings import CardEmbeddings


def batched_cosine_similarity(x: np.ndarray, y: Optional[np.ndarray] = None,
                              batch_size: int = 512) \
        -> Generator[Tuple[int, np.ndarray], None, None]:
    """Computes the pairwise cosine similarity of matrices in a memory efficient manner by
    batching computations. Yields a 2-tuple containing the zero-based row offset and a
    cosine similarity matrix of shape (batch_size, None).

    Args:
        - x: first matrix.
        - y: second matrix.
        - batch_size: number of operations to do at once.

    Preconditions:
        - x.shape[1] == y.shape[1]
    """
    # If y is not specified, use the input matrix.
    # In this case, we are computing the pairwise cosine similarity
    # for all rows of the input matrix.
    if y is None:
        y = x

    for row_index in range(0, int(x.shape[0] / batch_size) + 1):
        start = row_index * batch_size
        end = min([(row_index + 1) * batch_size, x.shape[0]])
        if end <= start:
            break

        # Compute a chunk of the similarity matrix.
        rows = x[start: end]
        similarity = metrics.pairwise.cosine_similarity(rows, y)
        yield (start, similarity)


def build_infinity_hop_graph(embeddings: CardEmbeddings, alpha: float = 0.50,
                             batch_size: int = 256) -> nx.Graph:
    """Builds the infinity-hop graph for a word embeddings space.

    Args:
        embeddings: The word embeddings to generate the graph for.
        alpha: The similarity threshold. Words that have a cosine similarity
            of at least this threshold are kept, and the rest are discarded.
        batch_size: Number of rows to batch in a single operation when computing
            the cosine similarity matrix.
    """
    graph = nx.Graph()
    logger.info('Generating infinity-hop graph')
    weights = embeddings.weights.astype(np.float32)
    # Compute the cosine similarity between all pairs of embedding vector.
    similarity_batches = batched_cosine_similarity(
        embeddings.weights,
        batch_size=batch_size
    )

    # Generate the infinity-hop network
    num_batches = int(embeddings.weights.shape[0] / batch_size) + 1
    for row_offset, similarities in tqdm.tqdm(similarity_batches, total=num_batches):
        # Filter out similarity scores that are less than the threshold
        pairs = np.argwhere(similarities >= alpha)
        for pair in pairs:
            i, j = pair
            if i == j:
                continue

            # The weight of the edge is the cosine similary.
            graph.add_edge(
                i + row_offset, j,
                weight=similarities[i][j]
            )

    return graph


def build_k_hop_graph(embeddings: CardEmbeddings, target_word: str,
                      k: int, alpha: float = 0.50) -> nx.Graph:
    """Builds the k-hop graph for a word embeddings space.

    Args:
        embeddings: The word embeddings to generate the graph for.
        target_word: The word of interest.
        k: The number of 'hops' between the word of interest and every node
            in the graph. The resultant graph has the property that the word
            of interest is reachable from any node in at most k edges.
        alpha: The similarity threshold. Words that have a cosine similarity
            of at least this threshold are kept, and the rest are discarded.
    """
    # Verify the alpha threshold is <= max(similarity between interest word).
    max_alpha = embeddings.most_similar(target_word, k=1)[0][1]
    if alpha > max_alpha:
        raise ValueError('Alpha threshold too high! The word of interest was not included '
                         'in the graph. For the given target word, '
                         '\'{}\', alpha can be AT MOST {}!'.format(target_word, max_alpha))

    graph = build_infinity_hop_graph(embeddings, alpha)

    # Get the word index of the word of interest.
    T = embeddings._vocabulary[target_word]

    # Compute the shortest paths from the word of interest to all reachable nodes.
    logger.info('Computing shortest paths')
    paths = nx.single_source_shortest_path_length(graph, T)

    logger.info('Building k-hop graph')
    nodes_to_delete = set()
    for node in tqdm.tqdm(graph.nodes):
        # Remove the node if the word of interest is not reachable in at most k edges.
        if node not in paths or paths[node] > k:
            nodes_to_delete.add(node)

    for node in nodes_to_delete:
        graph.remove_node(node)

    logger.info('Generated k-hop graph (nodes: {}, edges: {})'.format(
        len(graph.nodes), len(graph.edges)
    ))
    return graph


def draw_k_hop_graph(embeddings: CardEmbeddings, target_word: str,
                     k: int, alpha: float = 0.50,
                     min_node_size: float = 20,
                     max_node_size: float = 120,
                     min_font_size: float = 6,
                     max_font_size: float = 24,
                     node_alpha: float = 1,
                     edge_alpha: float = 0.05,
                     target_word_label_colour: str = 'black',
                     community_colour_map: str = 'plasma') -> None:
    """Draw the k-hop graph for the given word embeddings and interest word.
    This function DOES NOT show the matplotlib plot.

    Args:
        embeddings: The word embeddings to generate the graph for.
        target_word: The word of interest.
        k: The number of 'hops' between the word of interest and every node
            in the graph. The resultant graph has the property that the word
            of interest is reachable from any node in at most k edges.
        alpha: The similarity threshold. Words that have a cosine similarity
            of at least this threshold are kept, and the rest are discarded.
        min_node_size: The minimum size of a node, in pixels.
        max_node_size: The maximum size of a node, in pixels.
        min_font_size: The minimum size of a label, in pixels.
        max_font_size: The maximum size of a label, in pixels.
        node_alpha: The alpha/transparency to draw nodes with.
        edge_alpha: The alpha/transparency to draw edges with.
        target_word_label_colour: The colour of the target word label.
            Makes the target word stand out. Useless when there are many words.
        community_colour_map: The colour map to use when assigning colours to communities.
    """
    if alpha is None:
        _, similarity = embeddings.most_similar(target_word, k=1)[0]
        alpha = similarity - 0.05
        logger.info('No alpha threshold provided. Using alpha = {}'.format(alpha))

    graph = build_k_hop_graph(embeddings, target_word, k, alpha=alpha)

    logger.info('Computing best partition (Louvain community detection)')
    # compute the best partition
    partition = community_louvain.best_partition(graph)

    logger.info('Computing layout (ForceAtlas2)')
    forceatlas2 = ForceAtlas2(
        outboundAttractionDistribution=True,
        edgeWeightInfluence=1.0,
        jitterTolerance=1.0,
        barnesHutOptimize=True,
        barnesHutTheta=1.2,
        scalingRatio=2.0,
        strongGravityMode=False,
        gravity=1.0,
        verbose=False
    )

    positions = forceatlas2.forceatlas2_networkx_layout(graph)

    logger.info('Rendering graph with matplotlib')
    cmap = cm.get_cmap(community_colour_map, max(partition.values()) + 1)

    degrees = dict(graph.degree)
    max_degree = max(degrees.values())
    size_multipliers = {i: degrees[i] / max_degree for i in positions}

    # Generate node sizes
    node_size = [
        max(max_node_size * size_multipliers[i], min_node_size)
        for i in positions
    ]

    # Draw the nodes
    nx.draw_networkx_nodes(
        graph,
        positions,
        partition.keys(),
        node_size=node_size,
        cmap=cmap,
        node_color=list(partition.values()),
        alpha=node_alpha
    )

    # Draw the edges with a bezier curve
    curves = curved_edges(graph, positions)
    # Remove nan values
    curves = np.nan_to_num(curves)

    # Assign a colour to each edge, based on the community of the source node.
    edge_color = [cmap(partition[a]) for a, _ in graph.edges]
    edge_lines = LineCollection(curves, color=edge_color, cmap=cmap, alpha=edge_alpha, linewidths=1)
    plt.gca().add_collection(edge_lines)

    # Draw node labels (words)
    for i, (x, y) in positions.items():
        # The size of the label is proportional to the degree of the node.
        fontsize = max(max_font_size * size_multipliers[i]**4, min_font_size)
        word = embeddings.words[i]
        colour = target_word_label_colour if word == target_word else 'black'
        plt.text(x, y, word, fontsize=fontsize, ha='center', va='center', color=colour)


def visualise_k_hop_graph(target_word: str,
                          checkpoint: Optional[Union[str, Path]] = None,
                          weights_filepath: Optional[Union[str, Path]] = None,
                          vocab_filepath: Optional[Union[str, Path]] = None,
                          k: int = 2,
                          alpha: float = None,
                          min_node_size: float = 20,
                          max_node_size: float = 120,
                          min_font_size: float = 6,
                          max_font_size: float = 24,
                          node_alpha: float = 1,
                          edge_alpha: float = 0.15,
                          target_word_label_colour: str = 'black',
                          colour_map: str = 'tab20c',
                          output_path: Optional[Union[str, Path]] = None,
                          figure_width: int = 800,
                          figure_height: int = 600,
                          figure_dpi: int = 96,
                          export_dpi: int = 96,
                          verbose: bool = False) -> None:
    """Visualise the k-hop graph for the given word embeddings and interest word.
    Requires one of checkpoint / (weights_filepath and vocab_filepath).

    If output_path is specified, then no preview window is drawn.
    """
    # Ensure that at least on data argument was provided
    if checkpoint is None and weights_filepath is None and vocab_filepath is None:
        logger.error('One of checkpoint / (weights-filepath and vocab-filepath) is required!')
        exit(1)

    if checkpoint is not None:
        checkpoint = Path(checkpoint)
        weights_filepath = checkpoint / 'proj_weights.npy'
        vocab_filepath = checkpoint / 'vocab.txt'
    else:
        weights_filepath = Path(weights_filepath)
        vocab_filepath = Path(vocab_filepath)

    if not verbose:
        logger.setLevel(logging.ERROR)

    embeddings = WordEmbeddings(
        weights_filepath, vocab_filepath,
        name_metadata=weights_filepath.parent.stem
    )

    figsize = (figure_width / figure_dpi, figure_height / figure_dpi)
    plt.figure(figsize=figsize, dpi=figure_dpi)

    draw_k_hop_graph(
        embeddings,
        target_word,
        k,
        alpha=alpha,
        min_node_size=min_node_size,
        max_node_size=max_node_size,
        min_font_size=min_font_size,
        max_font_size=max_font_size,
        node_alpha=node_alpha,
        edge_alpha=edge_alpha,
        target_word_label_colour=target_word_label_colour,
        community_colour_map=colour_map
    )

    # Show the plot, or output it, depending on the mode.
    plt.axis('off')
    if not output_path:
        plt.show()
    else:
        output_path = Path(output_path)

        output_format = (output_path.suffix or 'png').replace('.', '')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_format == 'tex' or output_format == 'latex':
            tikzplotlib.save(output_path)
        else:
            plt.savefig(output_path, dpi=export_dpi)
        logger.info('Exported figure to {}'.format(output_path))


def main(args: argparse.Namespace) -> None:
    """Main entrypoint for the script."""
    visualise_k_hop_graph(**vars(args))


if __name__ == '__main__':
    # import python_ta
    # python_ta.check_all(config={
    #     'extra-imports': [
    #         'tqdm',
    #         'logging',
    #         'argparse',
    #         'pathlib',
    #         'typing',
    #         'numpy',
    #         'networkx',
    #         'matplotlib.cm',
    #         'matplotlib.pyplot',
    #         'matplotlib.collections',
    #         'community',
    #         'fa2',
    #         'sklearn.metrics',
    #         'curved_edges',
    #         'word_embeddings',
    #         'logger',
    #     ],
    #     'allowed-io': [''],
    #     'max-line-length': 100,
    #     'disable': ['R1705', 'C0200', 'W0612']
    # })

    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()

    parser = argparse.ArgumentParser(description='A tool for visualising k-hop graphs.')
    parser.add_argument('target_word', type=str, help='The word of interest.')
    # Preview and export configuration
    parser.add_argument('-o', '--output', dest='output_path', type=Path, default=None,
                        help='The file to write the figure to.')
    parser.add_argument('-fw', '--figure-width', type=int, default=800,
                        help='The width of the exported file.')
    parser.add_argument('-fh', '--figure-height', type=int, default=600,
                        help='The heght of the exported file.')
    parser.add_argument('-dpi', '--figure-dpi', type=int, default=96,
                        help='The DPI of the exported file.')
    parser.add_argument('-edpi', '--export-dpi', type=int, default=96,
                        help='The DPI of the exported file.')
    parser.add_argument('--verbose', action='store_true', help='Whether to log messages.')
    # Card Embeddings location
    parser.add_argument('--checkpoint', type=Path, default=None,
                        help='Path to a checkpoint directory containing a numpy file with '
                             'the trained embedding weights (proj_weights.npy) and a text '
                             'file with the model vocabulary (vocab.txt)')
    parser.add_argument('-w', '--weights-filepath', type=Path, default=None,
                        help='Path to a numpy file containing the trained embedding weights. '
                             'Use this instead of specifying the checkpoint directory.')
    parser.add_argument('-v', '--vocab-filepath', type=Path, default=None,
                        help='Path to a text file containing the model vocabulary. '
                             'Use this instead of specifying the checkpoint directory.')
    # K-hop Graph configuration
    parser.add_argument('--k', type=int, default=2, help='The number of \'hops\' between '
                        'the word of interest and every node in the graph.')
    parser.add_argument('--alpha', type=float, default=None,
                        help='The similarity threshold. If unspecified, defaults to 0.05 '
                        'less than the cosine similarity of the most similar word to the '
                        'word of interest.')
    parser.add_argument('--min-node-size', type=float, default=20,
                        help='The minimum size of a node.')
    parser.add_argument('--max-node-size', type=float, default=120,
                        help='The maximum size of a node.')
    parser.add_argument('--min-font-size', type=float, default=6,
                        help='The minimum size of a label.')
    parser.add_argument('--max-font-size', type=float, default=24,
                        help='The minimum size of a label.')
    parser.add_argument('--node-alpha', type=float, default=1,
                        help='The alpha/transparency to draw nodes with.')
    parser.add_argument('--edge-alpha', type=float, default=0.15,
                        help='The alpha/transparency to draw edges with.')
    parser.add_argument('--target-word-label-colour', type=str, default='black',
                        help='The colour of the target word label.')
    parser.add_argument('-cmap', '--colour-map', type=str, default='plasma')
    main(parser.parse_args())

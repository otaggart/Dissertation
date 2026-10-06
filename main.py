import pandas as pd
import networkx as nx
from collections import Counter
from networkx.algorithms import community as nx_community
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv("battle_royale_games_clean.csv")
print(df.head())


df["tropes"] = (
    df["tropes"]
    .fillna("")
    .apply(lambda x: [t.strip() for t in x.split(";") if t.strip()])
)


G = nx.Graph()

for tropes in df["tropes"]:
    for i in range(len(tropes)):
        for j in range(i + 1, len(tropes)):
            t1, t2 = tropes[i], tropes[j]
            if G.has_edge(t1, t2):
                G[t1][t2]["weight"] += 1
            else:
                G.add_edge(t1, t2, weight=1)

# Basic graph stats
print("\n=== GRAPH SUMMARY ===")
print("Nodes:", G.number_of_nodes())
print("Edges:", G.number_of_edges())
print("Density:", nx.density(G))
print("Average degree:", sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0)
print("Average clustering coefficient:", nx.average_clustering(G) if G.number_of_nodes() > 0 else 0)
print("Connected components:", nx.number_connected_components(G) if G.number_of_nodes() > 0 else 0)

# Node-level metrics
degree_centrality = nx.degree_centrality(G)
weighted_degree = dict(G.degree(weight="weight"))
betweenness_centrality = nx.betweenness_centrality(G) if G.number_of_nodes() > 0 else {}


all_tropes = [trope for tropes in df["tropes"] for trope in tropes]
trope_counts = Counter(all_tropes)

print("\n=== TOP TROPE FREQUENCIES ===")
for trope, count in trope_counts.most_common(10):
    print(f"{trope}: {count}")

print("\n=== TOP TROPES BY WEIGHTED DEGREE ===")
for trope, score in sorted(weighted_degree.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{trope}: {score}")

print("\n=== TOP TROPES BY DEGREE CENTRALITY ===")
for trope, score in sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{trope}: {score:.4f}")

print("\n=== TOP TROPES BY BETWEENNESS CENTRALITY ===")
for trope, score in sorted(betweenness_centrality.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"{trope}: {score:.4f}")


print("\n=== STRONGEST EDGES ===")
strongest_edges = sorted(G.edges(data=True), key=lambda x: x[2].get("weight", 1), reverse=True)[:15]
for u, v, data in strongest_edges:
    print(f"{u} -- {v}: weight={data['weight']}")


print("\n=== COMMUNITIES ===")
if G.number_of_nodes() > 0 and G.number_of_edges() > 0:
    communities = list(nx_community.greedy_modularity_communities(G))
    print("Number of communities:", len(communities))
    for i, comm in enumerate(sorted(communities, key=len, reverse=True), start=1):
        print(f"Community {i} ({len(comm)} nodes): {', '.join(sorted(comm))}")
else:
    print("Not enough data to detect communities.")



threshold = 3  # adjust if needed
G_filtered = nx.Graph(
    (u, v, d) for u, v, d in G.edges(data=True) if d["weight"] >= threshold
)

# Node sizes based on weighted degree
weighted_degree = dict(G.degree(weight="weight"))
node_sizes = [weighted_degree[n] * 50 for n in G_filtered.nodes()]

# Edge widths based on weight
edge_widths = [G_filtered[u][v]["weight"] for u, v in G_filtered.edges()]

# Layout
pos = nx.spring_layout(G_filtered, k=0.5, seed=42)

# Draw graph
plt.figure(figsize=(12, 12))

nx.draw_networkx_nodes(
    G_filtered, pos,
    node_size=node_sizes
)

nx.draw_networkx_edges(
    G_filtered, pos,
    width=edge_widths,
    alpha=0.6
)

nx.draw_networkx_labels(
    G_filtered, pos,
    font_size=8
)

plt.title("Battle Royale Trope Co-occurrence Network")
plt.axis("off")

plt.tight_layout()
plt.savefig("trope_network.png", dpi=300)
plt.show()
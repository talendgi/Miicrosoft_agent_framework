from __future__ import annotations

from collections import defaultdict, deque

from app.schemas.studio import EdgeDefinition, NodeDefinition


class WorkflowCompiler:
    def compile(self, nodes: list[NodeDefinition], edges: list[EdgeDefinition]) -> list[NodeDefinition]:
        if not nodes:
            return []

        indegree = defaultdict(int)
        adjacency = defaultdict(list)
        node_map = {node.id: node for node in nodes}

        for edge in edges:
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] += 1
            indegree.setdefault(edge.source, 0)

        queue = deque([node_id for node_id in node_map if indegree[node_id] == 0])
        ordered: list[NodeDefinition] = []

        while queue:
            current = queue.popleft()
            ordered.append(node_map[current])
            for neighbor in adjacency[current]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(nodes):
            raise ValueError("Workflow contains a cycle or disconnected dependencies.")

        return ordered


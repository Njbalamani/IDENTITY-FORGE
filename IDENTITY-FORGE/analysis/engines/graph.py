import networkx as nx

from access.models import AccessEvent, Role
from identities.models import IdentityProfile


class AccessGraphEngine:
    def __init__(self, organization):
        self.organization = organization

    def build_graph(self):
        graph = nx.DiGraph()
        from django.contrib.auth import get_user_model

        users = get_user_model().objects.filter(organization=self.organization)
        roles = Role.objects.filter(organization=self.organization).prefetch_related(
            "permissions", "inherits"
        )
        from identities.models import Team

        teams = Team.objects.filter(organization=self.organization)
        from access.models import AccessResource

        resources = AccessResource.objects.filter(organization=self.organization).prefetch_related(
            "permissions"
        )

        for user in users:
            profile = IdentityProfile.objects.filter(
                user=user, organization=self.organization
            ).first()
            graph.add_node(
                f"user:{user.id}",
                kind="user",
                label=user.username,
                risk_score=profile.risk_score if profile else 0,
                detail=user.display_name or user.username,
            )
        for role in roles:
            graph.add_node(
                f"role:{role.id}",
                kind="role",
                label=role.name,
                risk_score=role.risk_weight * (3 if role.is_privileged else 1),
                detail=role.code,
            )
        for team in teams:
            graph.add_node(
                f"team:{team.id}", kind="team", label=team.name, risk_score=1, detail=team.name
            )
        for resource in resources:
            graph.add_node(
                f"resource:{resource.id}",
                kind="resource",
                label=resource.name,
                risk_score=8 if resource.high_risk else 2,
                detail=resource.get_sensitivity_display(),
            )
        permissions = {permission for role in roles for permission in role.permissions.all()}
        permissions.update(
            permission for resource in resources for permission in resource.permissions.all()
        )
        for permission in permissions:
            graph.add_node(
                f"permission:{permission.id}",
                kind="permission",
                label=permission.code,
                risk_score=permission.risk_weight,
                detail=permission.get_category_display(),
            )

        from access.models import RoleAssignment

        for assignment in RoleAssignment.objects.filter(
            active=True, role__organization=self.organization
        ).select_related("user", "role", "team"):
            risky = (
                assignment.role.is_privileged
                or assignment.role.permissions.filter(is_high_risk=True).exists()
            )
            graph.add_edge(
                f"user:{assignment.user_id}",
                f"role:{assignment.role_id}",
                type="ASSIGNED",
                risky=risky,
                label="assigned",
            )
            if assignment.team_id:
                graph.add_edge(
                    f"user:{assignment.user_id}",
                    f"team:{assignment.team_id}",
                    type="MEMBER",
                    risky=False,
                    label="member",
                )
                graph.add_edge(
                    f"team:{assignment.team_id}",
                    f"role:{assignment.role_id}",
                    type="TEAM_ROLE",
                    risky=risky,
                    label="team role",
                )

        for role in roles:
            for parent in role.inherits.all():
                graph.add_edge(
                    f"role:{role.id}",
                    f"role:{parent.id}",
                    type="INHERITS",
                    risky=parent.is_privileged,
                    label="inherits",
                )
            for permission in role.permissions.all():
                graph.add_edge(
                    f"role:{role.id}",
                    f"permission:{permission.id}",
                    type="GRANTS",
                    risky=permission.is_high_risk,
                    label="grants",
                )

        for resource in resources:
            for permission in resource.permissions.all():
                graph.add_edge(
                    f"resource:{resource.id}",
                    f"permission:{permission.id}",
                    type="REQUIRES",
                    risky=permission.is_high_risk,
                    label="requires",
                )
                graph.add_edge(
                    f"permission:{permission.id}",
                    f"resource:{resource.id}",
                    type="ALLOWS",
                    risky=permission.is_high_risk or resource.high_risk,
                    label="allows",
                )

        for event in AccessEvent.objects.filter(
            organization=self.organization, resource__isnull=False
        ).select_related("user", "resource")[:600]:
            if (
                event.user_id
                and f"user:{event.user_id}" in graph
                and f"resource:{event.resource_id}" in graph
            ):
                graph.add_edge(
                    f"user:{event.user_id}",
                    f"resource:{event.resource_id}",
                    type="ACCESSED",
                    risky=event.resource.high_risk or not event.success,
                    label="accessed",
                )
        return graph

    def to_payload(self, graph=None):
        graph = graph or self.build_graph()
        layout = (
            nx.spring_layout(graph, dim=3, seed=42, iterations=48, k=0.55)
            if graph.number_of_nodes()
            else {}
        )
        nodes = []
        for node_id, data in graph.nodes(data=True):
            position = layout.get(node_id, (0, 0, 0))
            nodes.append(
                {
                    "id": node_id,
                    "label": data.get("label", node_id),
                    "kind": data.get("kind", "unknown"),
                    "detail": data.get("detail", ""),
                    "risk_score": data.get("risk_score", 0),
                    "x": round(float(position[0]), 4),
                    "y": round(float(position[1]), 4),
                    "z": round(float(position[2]), 4),
                }
            )
        links = [
            {
                "source": source,
                "target": target,
                "type": data.get("type", "RELATED"),
                "risky": bool(data.get("risky", False)),
                "label": data.get("label", ""),
            }
            for source, target, data in graph.edges(data=True)
        ]
        return {
            "nodes": nodes,
            "links": links,
            "summary": {
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                "risky_edge_count": sum(1 for link in links if link["risky"]),
            },
        }

    def indirect_paths(self, graph, user):
        user_id = getattr(user, "id", user)
        source = f"user:{user_id}"
        if source not in graph:
            return []
        results = []
        for node_id, data in graph.nodes(data=True):
            if data.get("kind") != "resource" or not nx.has_path(graph, source, node_id):
                continue
            candidates = list(nx.all_simple_paths(graph, source, node_id, cutoff=6))
            scored = []
            for path in candidates:
                risky_nodes = [
                    graph.nodes[node]["label"]
                    for node in path
                    if graph.nodes[node].get("kind") == "role"
                    and graph.nodes[node].get("risk_score", 0) >= 3
                ]
                if len(path) > 2 or risky_nodes:
                    scored.append((len(path), risky_nodes, path))
            if not scored:
                continue
            _, risky_nodes, path = max(scored, key=lambda item: (item[0], len(item[1])))
            results.append(
                {
                    "target": data.get("label"),
                    "path": [graph.nodes[node].get("label", node) for node in path],
                    "hop_count": len(path) - 1,
                    "risky_roles": risky_nodes,
                    "path_count": len(candidates),
                }
            )
        return results

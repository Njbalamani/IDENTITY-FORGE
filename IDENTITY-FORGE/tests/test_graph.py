from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import User
from analysis.engines.graph import AccessGraphEngine
from tests.factories import (
    assign_role,
    create_event,
    create_organization,
    create_permission,
    create_resource,
    create_role,
    create_user,
)


class AccessGraphTests(TestCase):
    def setUp(self):
        self.organization = create_organization()
        self.permission = create_permission(
            self.organization,
            "DATA_EXPORT",
            risk_weight=9,
            is_high_risk=True,
        )
        self.role = create_role(
            self.organization,
            "analyst",
            "Analyst",
            permissions=[self.permission],
            risk_weight=3,
        )
        self.user = create_user(
            self.organization,
            "graph@example.invalid",
            platform_role=User.PlatformRole.SECURITY_ANALYST,
        )
        assign_role(self.user, self.role)
        self.resource = create_resource(
            self.organization,
            "claims-warehouse",
            permissions=[self.permission],
        )
        create_event(self.user, resource=self.resource)
        self.engine = AccessGraphEngine(self.organization)

    def test_graph_contains_expected_nodes_and_edges(self):
        graph = self.engine.build_graph()
        self.assertIn(f"user:{self.user.id}", graph)
        self.assertIn(f"role:{self.role.id}", graph)
        self.assertIn(f"resource:{self.resource.id}", graph)
        self.assertIn(f"permission:{self.permission.id}", graph)
        edge_types = {data["type"] for _, _, data in graph.edges(data=True)}
        self.assertTrue(
            {"ASSIGNED", "GRANTS", "REQUIRES", "ALLOWS", "ACCESSED"}.issubset(edge_types)
        )

    def test_payload_contains_three_dimensional_positions(self):
        payload = self.engine.to_payload()
        self.assertEqual(payload["summary"]["node_count"], len(payload["nodes"]))
        sample = payload["nodes"][0]
        for key in ("x", "y", "z"):
            self.assertIn(key, sample)

    def test_indirect_path_from_user_to_resource(self):
        graph = self.engine.build_graph()
        paths = self.engine.indirect_paths(graph, self.user)
        self.assertTrue(paths)
        self.assertEqual(paths[0]["target"], "claims-warehouse")
        self.assertIn("Analyst", paths[0]["path"])

    def test_graph_api_is_organization_scoped(self):
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get("/api/graph/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        labels = [node["label"] for node in response.data["nodes"]]
        self.assertIn("graph@example.invalid", labels)

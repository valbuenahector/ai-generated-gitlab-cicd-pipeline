import pytest
import requests_mock
import json
import os
from workload_manager import VolterraWorkloadManager

@pytest.fixture
def manager():
    return VolterraWorkloadManager(
        api_url="https://test.console.ves.volterra.io/api",
        api_token="test-token",
        tenant="test-tenant",
        namespace="test-namespace"
    )

def test_create_workload(manager):
    with requests_mock.Mocker() as m:
        m.post(
            "https://test.console.ves.volterra.io/api/config/namespaces/test-namespace/workloads",
            json={"metadata": {"name": "test-workload"}},
            status_code=200
        )
        result = manager.create_workload(
            name="test-workload",
            image="test-image",
            site_name="test-site",
            port=8080,
            container_registry_name="test-registry"
        )
        assert result["metadata"]["name"] == "test-workload"
        assert m.called
        assert m.request_history[0].headers["Authorization"] == "Ves-io-api-key test-token"
        
        payload = m.request_history[0].json()
        assert payload["spec"]["service"]["deploy_options"]["deploy_ce_virtual_sites"]["virtual_site"][0]["name"] == "test-site"

def test_replace_workload(manager):
    with requests_mock.Mocker() as m:
        m.put(
            "https://test.console.ves.volterra.io/api/config/namespaces/test-namespace/workloads/test-workload",
            json={"metadata": {"name": "test-workload"}},
            status_code=200
        )
        result = manager.replace_workload(
            name="test-workload",
            image="test-image",
            site_name="test-site",
            port=8080,
            container_registry_name="test-registry"
        )
        assert result["metadata"]["name"] == "test-workload"
        assert m.called
        assert m.request_history[0].method == "PUT"

def test_get_workload(manager):
    with requests_mock.Mocker() as m:
        m.get(
            "https://test.console.ves.volterra.io/api/config/namespaces/test-namespace/workloads/test-workload",
            json={"metadata": {"name": "test-workload"}},
            status_code=200
        )
        result = manager.get_workload("test-workload")
        assert result["metadata"]["name"] == "test-workload"
        assert m.called

def test_delete_workload(manager):
    with requests_mock.Mocker() as m:
        m.delete(
            "https://test.console.ves.volterra.io/api/config/namespaces/test-namespace/workloads/test-workload",
            json={"status": "deleted"},
            status_code=200
        )
        result = manager.delete_workload("test-workload")
        assert result["status"] == "deleted"
        assert m.called
        assert m.request_history[0].method == "DELETE"

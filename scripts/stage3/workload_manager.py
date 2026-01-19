"""
F5 Distributed Cloud (F5XC) Workload Manager

This script provides a management interface for F5XC Workloads via the Volterra API.
It supports creating, replacing, getting, and deleting workloads on Customer Edge (CE) Virtual Sites.

Usage:
    python workload_manager.py [operation]

Operations:
    create  - Create a new workload
    replace - Replace an existing workload configuration
    get     - Retrieve workload details
    delete  - Delete a workload

Required Environment Variables (GitLab CI/CD):
    F5XC_API_URL       - The API endpoint URL (e.g., https://tenant.console.ves.volterra.io/api)
    F5XC_API_TOKEN     - Your F5XC API Token
    F5XC_TENANT        - Your F5XC Tenant name
    F5XC_NAMESPACE     - The F5XC Namespace to operate in
    F5XC_SITE_NAME     - The name of the Customer Edge Virtual Site
    F5XC_WORKLOAD_NAME - The name of the workload
    IMAGE_REF          - The container image reference (registry/image:tag)

Optional Environment Variables:
    F5XC_REGISTRY_NAME - Name of the container registry object (default: <namespace>-acr)
    F5XC_WORKLOAD_PORT - The port the workload listens on (default: 5000)

Example:
    export F5XC_API_URL="https://my-tenant.console.ves.volterra.io/api"
    export F5XC_API_TOKEN="xxxxxxxxxxxx"
    export F5XC_TENANT="my-tenant"
    export F5XC_NAMESPACE="my-ns"
    export F5XC_SITE_NAME="my-ce-vsite"
    export F5XC_WORKLOAD_NAME="my-app"
    export IMAGE_REF="my-registry.azurecr.io/my-app:v1"
    python workload_manager.py create
"""

import os
import requests
import json
import argparse
import sys

class VolterraWorkloadManager:
    def __init__(self, api_url, api_token, tenant, namespace):
        self.api_url = api_url.rstrip('/')
        self.api_token = api_token
        self.tenant = tenant
        self.namespace = namespace

    def _get_session(self):
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Ves-io-api-key {self.api_token}",
            "Content-Type": "application/json"
        })
        return session

    def _get_payload(self, name, image, site_name, port, container_registry_name):
        return {
            "metadata": {
                "name": name,
                "namespace": self.namespace,
                "labels": {},
                "annotations": {},
                "disable": False
            },
            "spec": {
                "service": {
                    "num_replicas": 1,
                    "containers": [
                        {
                            "name": name,
                            "image": {
                                "name": image,
                                "container_registry": {
                                    "tenant": f"{self.tenant}-qyyfhhfj" if "f5-amer-ent" in self.tenant else self.tenant,
                                    "namespace": self.namespace,
                                    "name": container_registry_name,
                                    "kind": "container_registry"
                                },
                                "pull_policy": "IMAGE_PULL_POLICY_DEFAULT"
                            },
                            "init_container": False,
                            "flavor": "CONTAINER_FLAVOR_TYPE_TINY",
                            "command": [],
                            "args": []
                        }
                    ],
                    "volumes": [],
                    "deploy_options": {
                        "deploy_ce_virtual_sites": {
                            "virtual_site": [
                                {
                                    "tenant": f"{self.tenant}-qyyfhhfj" if "f5-amer-ent" in self.tenant else self.tenant,
                                    "namespace": "shared",
                                    "name": site_name,
                                    "kind": "virtual_site"
                                }
                            ]
                        }
                    },
                    "advertise_options": {
                        "advertise_in_cluster": {
                            "port": {
                                "info": {
                                    "port": port,
                                    "protocol": "PROTOCOL_TCP",
                                    "same_as_port": {}
                                }
                            }
                        }
                    },
                    "family": {
                        "v4": {}
                    }
                }
            }
        }

    def create_workload(self, name, image, site_name, port, container_registry_name):
        url = f"{self.api_url}/config/namespaces/{self.namespace}/workloads"
        payload = self._get_payload(name, image, site_name, port, container_registry_name)
        
        session = self._get_session()
        response = session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def replace_workload(self, name, image, site_name, port, container_registry_name):
        url = f"{self.api_url}/config/namespaces/{self.namespace}/workloads/{name}"
        payload = self._get_payload(name, image, site_name, port, container_registry_name)
        
        session = self._get_session()
        response = session.put(url, json=payload)
        response.raise_for_status()
        return response.json()

    def get_workload(self, name):
        url = f"{self.api_url}/config/namespaces/{self.namespace}/workloads/{name}"
        session = self._get_session()
        response = session.get(url)
        response.raise_for_status()
        return response.json()

    def delete_workload(self, name):
        url = f"{self.api_url}/config/namespaces/{self.namespace}/workloads/{name}"
        session = self._get_session()
        # DeleteRequest can be empty or have name/namespace as per schema
        payload = {
            "name": name,
            "namespace": self.namespace
        }
        response = session.delete(url, json=payload)
        response.raise_for_status()
        return response.json() if response.text else {"status": "deleted"}

def main():
    parser = argparse.ArgumentParser(description='F5XC Workload Manager')
    parser.add_argument('operation', choices=['create', 'replace', 'delete', 'get'], help='Operation to perform')
    
    # Environment variables mapping
    api_url = os.getenv('F5XC_API_URL')
    api_token = os.getenv('F5XC_API_TOKEN')
    tenant = os.getenv('F5XC_TENANT')
    namespace = os.getenv('F5XC_NAMESPACE')
    site_name = os.getenv('F5XC_SITE_NAME')
    workload_name = os.getenv('F5XC_WORKLOAD_NAME')
    image_name = os.getenv('IMAGE_REF')
    # Assuming some defaults or additional env vars for these
    container_registry_name = os.getenv('F5XC_REGISTRY_NAME', f"{namespace}-acr")
    port = int(os.getenv('F5XC_WORKLOAD_PORT', '5000'))

    if not all([api_url, api_token, tenant, namespace]):
        print("Error: Missing required environment variables (F5XC_API_URL, F5XC_API_TOKEN, F5XC_TENANT, F5XC_NAMESPACE)")
        sys.exit(1)

    manager = VolterraWorkloadManager(api_url, api_token, tenant, namespace)
    args = parser.parse_args()

    try:
        if args.operation == 'create':
            print(f"Creating workload {workload_name}...")
            result = manager.create_workload(workload_name, image_name, site_name, port, container_registry_name)
            print(json.dumps(result, indent=2))
        elif args.operation == 'replace':
            print(f"Replacing workload {workload_name}...")
            result = manager.replace_workload(workload_name, image_name, site_name, port, container_registry_name)
            print(json.dumps(result, indent=2))
        elif args.operation == 'get':
            print(f"Getting workload {workload_name}...")
            result = manager.get_workload(workload_name)
            print(json.dumps(result, indent=2))
        elif args.operation == 'delete':
            print(f"Deleting workload {workload_name}...")
            result = manager.delete_workload(workload_name)
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        sys.exit(1)

if __name__ == "__main__":
    main()

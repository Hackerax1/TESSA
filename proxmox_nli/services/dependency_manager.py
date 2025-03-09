#!/usr/bin/env python3
"""
Dependency Manager for service dependencies in TESSA
Handles dependency resolution, visualization, and installation ordering
"""

import logging
from typing import Dict, List, Set, Tuple, Optional
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class DependencyManager:
    """
    Manages service dependencies for the TESSA service catalog.
    - Resolves dependency chains
    - Creates installation order lists
    - Detects circular dependencies
    - Visualizes dependency graphs
    """
    
    def __init__(self, service_catalog=None):
        """Initialize the dependency manager with a service catalog"""
        self.service_catalog = service_catalog
        self.dependency_graph = nx.DiGraph()
        
    def build_dependency_graph(self):
        """Build a directed graph of all service dependencies in the catalog"""
        if not self.service_catalog:
            logger.error("No service catalog provided to dependency manager")
            return False
            
        # Clear existing graph
        self.dependency_graph.clear()
        
        # Get all services
        services = self.service_catalog.get_all_services()
        
        # Add all services as nodes
        for service in services:
            service_id = service['id']
            self.dependency_graph.add_node(
                service_id, 
                name=service.get('name', service_id),
                description=service.get('description', '')
            )
            
        # Add dependencies as edges
        for service in services:
            service_id = service['id']
            
            if 'dependencies' in service:
                for dep in service.get('dependencies', []):
                    dep_id = dep['id']
                    required = dep.get('required', True)
                    description = dep.get('description', '')
                    
                    # Only add if the dependency exists as a node
                    if self.service_catalog.get_service(dep_id):
                        self.dependency_graph.add_edge(
                            service_id, dep_id, 
                            required=required,
                            description=description
                        )
        
        logger.info(f"Built dependency graph with {len(self.dependency_graph.nodes)} services and {len(self.dependency_graph.edges)} dependencies")
        return True
        
    def get_installation_order(self, service_id: str) -> List[str]:
        """
        Get the proper installation order for a service and its dependencies
        
        Args:
            service_id: The ID of the service to install
            
        Returns:
            List of service IDs in proper installation order
        """
        if not self.dependency_graph:
            self.build_dependency_graph()
            
        if service_id not in self.dependency_graph:
            logger.error(f"Service {service_id} not found in dependency graph")
            return []
            
        try:
            # Get all predecessors (dependencies) of the service
            predecessors = list(nx.dfs_predecessors(self.dependency_graph, service_id).values())
            
            # Add the service itself
            if service_id not in predecessors:
                predecessors.append(service_id)
                
            # Get topological sort for installation order
            # This ensures dependencies are installed before services that require them
            all_nodes = list(nx.topological_sort(self.dependency_graph))
            
            # Filter for only the services we need and maintain the topological order
            installation_order = [node for node in all_nodes if node in predecessors or node == service_id]
            
            return installation_order
            
        except nx.NetworkXUnfeasible:
            logger.error(f"Dependency graph contains cycles, cannot determine installation order for {service_id}")
            return []
            
    def detect_circular_dependencies(self) -> List[List[str]]:
        """
        Detect any circular dependencies in the service catalog
        
        Returns:
            List of cycles, each a list of service IDs in the cycle
        """
        if not self.dependency_graph:
            self.build_dependency_graph()
            
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                logger.warning(f"Detected {len(cycles)} circular dependencies in service catalog")
                for cycle in cycles:
                    logger.warning(f"Circular dependency: {' -> '.join(cycle)} -> {cycle[0]}")
            return cycles
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {str(e)}")
            return []
            
    def get_dependency_tree(self, service_id: str) -> Dict:
        """
        Get a hierarchical tree of dependencies for a service
        
        Args:
            service_id: The ID of the service to get dependencies for
            
        Returns:
            Nested dictionary representing the dependency tree
        """
        if not self.dependency_graph:
            self.build_dependency_graph()
            
        if service_id not in self.dependency_graph:
            return {}
            
        def build_tree(node, visited=None):
            if visited is None:
                visited = set()
                
            if node in visited:
                return {"id": node, "name": self.dependency_graph.nodes[node].get('name', node), "circular": True}
                
            visited.add(node)
            
            # Get immediate dependencies (successors in the graph)
            dependencies = []
            for dep in self.dependency_graph.successors(node):
                edge_data = self.dependency_graph.get_edge_data(node, dep)
                required = edge_data.get('required', True)
                
                dependencies.append({
                    "id": dep,
                    "name": self.dependency_graph.nodes[dep].get('name', dep),
                    "required": required,
                    "description": edge_data.get('description', ''),
                    "dependencies": build_tree(dep, visited.copy())
                })
                
            return dependencies
            
        # Build the tree starting with the requested service
        service_data = self.dependency_graph.nodes[service_id]
        tree = {
            "id": service_id,
            "name": service_data.get('name', service_id),
            "description": service_data.get('description', ''),
            "dependencies": build_tree(service_id)
        }
        
        return tree
        
    def visualize_dependencies(self, service_id: str = None, include_optional: bool = True) -> Optional[str]:
        """
        Generate a visualization of the dependency graph for a service
        
        Args:
            service_id: The ID of the service to visualize dependencies for (or None for all services)
            include_optional: Whether to include optional dependencies in the visualization
            
        Returns:
            Base64 encoded PNG image of the dependency graph or None if visualization fails
        """
        try:
            import networkx as nx
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("networkx or matplotlib not installed. Cannot visualize dependencies.")
            return None
        
        if not self.dependency_graph:
            self.build_dependency_graph()
            
        # Create a subgraph based on parameters
        if service_id:
            # Include all dependencies of the specified service
            try:
                # Get all ancestors (dependencies) of the service
                ancestors = list(nx.ancestors(self.dependency_graph, service_id))
                ancestors.append(service_id)  # Add the service itself
                
                # Create subgraph
                graph = self.dependency_graph.subgraph(ancestors)
            except nx.NetworkXError:
                logger.error(f"Service {service_id} not found in dependency graph")
                return None
        else:
            graph = self.dependency_graph
            
        # Filter edges based on required status if needed
        if not include_optional:
            edges_to_remove = [(u, v) for u, v, d in graph.edges(data=True) if not d.get('required', True)]
            graph = graph.copy()
            graph.remove_edges_from(edges_to_remove)
        
        # Generate the visualization
        plt.figure(figsize=(12, 8))
        
        # Node positions using a hierarchical layout
        pos = nx.spring_layout(graph)
        
        # Draw nodes
        nx.draw_networkx_nodes(graph, pos, node_size=500, node_color='lightblue')
        
        # Draw required edges in solid blue
        required_edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('required', True)]
        nx.draw_networkx_edges(graph, pos, edgelist=required_edges, width=2, edge_color='blue')
        
        # Draw optional edges in dashed gray
        if include_optional:
            optional_edges = [(u, v) for u, v, d in graph.edges(data=True) if not d.get('required', True)]
            nx.draw_networkx_edges(graph, pos, edgelist=optional_edges, width=1, style='dashed', edge_color='gray')
        
        # Draw labels
        nx.draw_networkx_labels(graph, pos)
        
        plt.axis('off')
        plt.title('Service Dependency Graph')
        
        # Save to BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        
        # Encode as base64
        image_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()
        
        return image_base64

    def can_install_service(self, service_id: str) -> Tuple[bool, str]:
        """
        Determine if a service can be installed based on its dependencies
        
        Args:
            service_id: The ID of the service to check
            
        Returns:
            (bool, str): Tuple of (can_install, reason)
        """
        if not self.service_catalog:
            return False, "No service catalog available"
            
        service = self.service_catalog.get_service(service_id)
        if not service:
            return False, f"Service {service_id} not found in catalog"
            
        # Check if service has dependencies
        if 'dependencies' not in service or not service['dependencies']:
            return True, "No dependencies required"
            
        # Check for each required dependency
        for dep in service['dependencies']:
            if dep.get('required', True):
                dep_service = self.service_catalog.get_service(dep['id'])
                if not dep_service:
                    return False, f"Required dependency {dep['id']} is missing from the service catalog"
        
        # Check for circular dependencies
        if not self.dependency_graph:
            self.build_dependency_graph()
            
        try:
            self.get_installation_order(service_id)
            return True, "All dependencies satisfied"
        except nx.NetworkXUnfeasible:
            return False, "Circular dependency detected"
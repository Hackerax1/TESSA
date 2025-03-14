"""
Service dependency visualization for Proxmox NLI.
Provides visualization of service dependencies and relationships.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Tuple, Set
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
from io import BytesIO
import base64

logger = logging.getLogger(__name__)

class DependencyVisualizer:
    """Visualizes service dependencies."""
    
    def __init__(self, dependency_manager):
        """Initialize the dependency visualizer.
        
        Args:
            dependency_manager: DependencyManager instance
        """
        self.dependency_manager = dependency_manager
        self.output_dir = os.path.join(os.path.dirname(__file__), 'data', 'visualizations')
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_dependency_graph(self, service_id: str = None, include_optional: bool = True, 
                                 output_format: str = 'png', highlight_service: str = None) -> Dict:
        """Generate a dependency graph for a service.
        
        Args:
            service_id: ID of the service to generate graph for, or None for all services
            include_optional: Whether to include optional dependencies
            output_format: Output format ('png', 'svg', or 'base64')
            highlight_service: Service ID to highlight in the graph
            
        Returns:
            Dictionary with graph information and path to generated image
        """
        try:
            # Build the dependency graph
            if service_id:
                # Generate graph for a specific service
                dependency_tree = self.dependency_manager.get_dependency_tree(service_id)
                graph = self._build_graph_from_tree(dependency_tree, include_optional, highlight_service)
                title = f"Dependencies for {dependency_tree.get('name', service_id)}"
            else:
                # Generate graph for all services
                graph = self.dependency_manager.build_dependency_graph()
                
                # Remove optional dependencies if requested
                if not include_optional:
                    edges_to_remove = [(u, v) for u, v, d in graph.edges(data=True) 
                                     if d.get('optional', False)]
                    graph.remove_edges_from(edges_to_remove)
                    
                title = "Complete Service Dependency Graph"
            
            # Check if graph is empty
            if len(graph.nodes()) == 0:
                return {
                    "success": False,
                    "message": "No dependencies found to visualize",
                    "explanation": "The selected service has no dependencies, or no services exist in the catalog."
                }
            
            # Generate the visualization
            output_path = None
            if output_format == 'base64':
                image_data = self._draw_graph(graph, title, return_base64=True)
                
                return {
                    "success": True,
                    "image_data": image_data,
                    "node_count": len(graph.nodes()),
                    "edge_count": len(graph.edges())
                }
            else:
                output_filename = f"dependencies_{service_id if service_id else 'all'}.{output_format}"
                output_path = os.path.join(self.output_dir, output_filename)
                self._draw_graph(graph, title, output_path=output_path)
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "node_count": len(graph.nodes()),
                    "edge_count": len(graph.edges())
                }
                
        except Exception as e:
            logger.error(f"Error generating dependency graph: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to generate dependency graph: {str(e)}"
            }
    
    def generate_service_map(self, services: List[str] = None, group_by: str = 'category',
                           output_format: str = 'png') -> Dict:
        """Generate a map of selected services.
        
        Args:
            services: List of service IDs to include, or None for all services
            group_by: How to group services ('category', 'goal', or None)
            output_format: Output format ('png', 'svg', or 'base64')
            
        Returns:
            Dictionary with map information and path to generated image
        """
        try:
            # Get all services if not specified
            if services is None:
                services = [s['id'] for s in 
                           self.dependency_manager.service_catalog.get_all_services()]
                
            # Filter to only existing services
            services = [s for s in services if 
                       self.dependency_manager.service_catalog.get_service(s) is not None]
                
            if not services:
                return {
                    "success": False,
                    "message": "No services found to visualize"
                }
                
            # Create the graph
            graph = nx.Graph()
            
            # Add nodes with attributes
            for service_id in services:
                service = self.dependency_manager.service_catalog.get_service(service_id)
                if not service:
                    continue
                    
                service_name = service.get('name', service_id)
                category = service.get('category', 'Other')
                
                # Get goals if available
                goals = []
                for goal in service.get('user_goals', []):
                    goals.append(goal['id'])
                    
                # Add to graph
                graph.add_node(service_id, 
                             name=service_name, 
                             category=category,
                             goals=goals)
            
            # Add edges for dependencies
            for service_id in services:
                dependencies = self.dependency_manager.service_catalog.get_service_dependencies(service_id)
                for dep in dependencies:
                    if dep['id'] in services:
                        graph.add_edge(service_id, dep['id'], 
                                     optional=not dep['required'],
                                     weight=2 if dep['required'] else 1)
            
            # Define node colors based on grouping
            node_colors = {}
            node_groups = {}
            
            if group_by == 'category':
                # Group by service category
                categories = set()
                for _, data in graph.nodes(data=True):
                    categories.add(data.get('category', 'Other'))
                
                # Assign colors to categories
                color_map = plt.cm.get_cmap('tab20', len(categories))
                for i, category in enumerate(categories):
                    node_groups[category] = []
                    node_colors[category] = color_map(i)
                
                # Group nodes
                for node, data in graph.nodes(data=True):
                    category = data.get('category', 'Other')
                    node_groups[category].append(node)
                    
            elif group_by == 'goal':
                # Group by primary goal
                goals = set()
                for _, data in graph.nodes(data=True):
                    if data.get('goals'):
                        # Use first goal as primary
                        goals.add(data.get('goals')[0])
                    else:
                        goals.add('Other')
                
                # Assign colors to goals
                color_map = plt.cm.get_cmap('tab20', len(goals))
                for i, goal in enumerate(goals):
                    node_groups[goal] = []
                    node_colors[goal] = color_map(i)
                
                # Group nodes
                for node, data in graph.nodes(data=True):
                    if data.get('goals'):
                        goal = data.get('goals')[0]
                    else:
                        goal = 'Other'
                    node_groups[goal].append(node)
            else:
                # No grouping, just assign random colors
                for node in graph.nodes():
                    group = node[0].upper()  # Use first letter as group
                    if group not in node_groups:
                        node_groups[group] = []
                        node_colors[group] = plt.cm.tab20(hash(group) % 20)
                    node_groups[group].append(node)
            
            # Generate title
            if len(services) == len(self.dependency_manager.service_catalog.get_all_services()):
                title = "Complete Service Map"
            else:
                title = f"Service Map ({len(services)} services)"
                
            # Generate the visualization
            if output_format == 'base64':
                image_data = self._draw_service_map(graph, title, node_colors, node_groups, return_base64=True)
                
                return {
                    "success": True,
                    "image_data": image_data,
                    "service_count": len(graph.nodes()),
                    "dependency_count": len(graph.edges())
                }
            else:
                output_filename = f"service_map_{group_by}.{output_format}"
                output_path = os.path.join(self.output_dir, output_filename)
                self._draw_service_map(graph, title, node_colors, node_groups, output_path=output_path)
                
                return {
                    "success": True,
                    "output_path": output_path,
                    "service_count": len(graph.nodes()),
                    "dependency_count": len(graph.edges())
                }
                
        except Exception as e:
            logger.error(f"Error generating service map: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to generate service map: {str(e)}"
            }
    
    def _build_graph_from_tree(self, dependency_tree: Dict, include_optional: bool = True,
                             highlight_service: str = None) -> nx.DiGraph:
        """Build a NetworkX graph from a dependency tree.
        
        Args:
            dependency_tree: Dependency tree dictionary
            include_optional: Whether to include optional dependencies
            highlight_service: Service ID to highlight
            
        Returns:
            NetworkX DiGraph instance
        """
        graph = nx.DiGraph()
        
        # Add the root service
        root_id = dependency_tree.get('id')
        root_name = dependency_tree.get('name', root_id)
        graph.add_node(root_id, name=root_name, 
                     highlight=(root_id == highlight_service))
        
        # Process dependencies recursively
        self._process_dependencies(graph, root_id, dependency_tree.get('dependencies', []), 
                               include_optional, highlight_service, processed=set())
        
        return graph
    
    def _process_dependencies(self, graph: nx.DiGraph, parent_id: str, dependencies: List[Dict],
                           include_optional: bool, highlight_service: str = None,
                           processed: Set[str] = None):
        """Process dependencies recursively.
        
        Args:
            graph: NetworkX graph to add nodes and edges to
            parent_id: ID of the parent service
            dependencies: List of dependency dictionaries
            include_optional: Whether to include optional dependencies
            highlight_service: Service ID to highlight
            processed: Set of already processed service IDs
        """
        if processed is None:
            processed = set()
        
        for dep in dependencies:
            dep_id = dep.get('id')
            dep_name = dep.get('name', dep_id)
            required = dep.get('required', True)
            
            # Skip optional dependencies if not included
            if not include_optional and not required:
                continue
                
            # Avoid cycles
            if dep_id in processed:
                continue
                
            # Add to processed set
            processed.add(dep_id)
                
            # Add node if not already in graph
            if dep_id not in graph:
                graph.add_node(dep_id, name=dep_name, 
                             highlight=(dep_id == highlight_service))
                
            # Add edge
            graph.add_edge(parent_id, dep_id, optional=not required,
                         weight=2 if required else 1)
            
            # Process nested dependencies if present
            if 'dependencies' in dep:
                self._process_dependencies(graph, dep_id, dep.get('dependencies', []), 
                                       include_optional, highlight_service, processed)
    
    def _draw_graph(self, graph: nx.Graph, title: str, output_path: str = None,
                  return_base64: bool = False) -> Optional[str]:
        """Draw a NetworkX graph.
        
        Args:
            graph: NetworkX graph to draw
            title: Title for the graph
            output_path: Path to save the image to, or None
            return_base64: Whether to return base64-encoded image data
            
        Returns:
            Base64-encoded image data if return_base64 is True, otherwise None
        """
        plt.figure(figsize=(12, 8))
        plt.title(title, fontsize=16)
        
        # Get position layout
        pos = nx.spring_layout(graph, k=0.3, iterations=50)
        
        # Draw nodes
        node_colors = []
        for node in graph.nodes():
            if graph.nodes[node].get('highlight', False):
                node_colors.append('red')
            else:
                node_colors.append('lightblue')
                
        nx.draw_networkx_nodes(graph, pos, node_size=1500, node_color=node_colors, alpha=0.8)
        
        # Draw edges with different styles for optional vs required
        required_edges = [(u, v) for u, v, d in graph.edges(data=True) 
                        if not d.get('optional', False)]
        optional_edges = [(u, v) for u, v, d in graph.edges(data=True) 
                        if d.get('optional', False)]
        
        nx.draw_networkx_edges(graph, pos, edgelist=required_edges, width=2, arrowsize=20)
        nx.draw_networkx_edges(graph, pos, edgelist=optional_edges, width=1.5, 
                             style='dashed', alpha=0.7, arrowsize=15)
        
        # Draw labels with service names
        labels = {node: data.get('name', node) for node, data in graph.nodes(data=True)}
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=10, 
                              font_family='sans-serif')
        
        # Add legend
        plt.plot([0], [0], color='black', linestyle='-', label='Required Dependency')
        plt.plot([0], [0], color='black', linestyle='--', label='Optional Dependency')
        if any(data.get('highlight', False) for _, data in graph.nodes(data=True)):
            plt.scatter([0], [0], color='red', s=100, label='Highlighted Service')
        plt.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='gray')
        
        plt.axis('off')  # Turn off the axis
        
        if return_base64:
            # Return as base64 string
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close()
            return img_base64
        elif output_path:
            # Save to file
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            return None
    
    def _draw_service_map(self, graph: nx.Graph, title: str, node_colors: Dict,
                       node_groups: Dict, output_path: str = None,
                       return_base64: bool = False) -> Optional[str]:
        """Draw a service map with grouped nodes.
        
        Args:
            graph: NetworkX graph to draw
            title: Title for the graph
            node_colors: Dictionary mapping groups to colors
            node_groups: Dictionary mapping groups to lists of nodes
            output_path: Path to save the image to, or None
            return_base64: Whether to return base64-encoded image data
            
        Returns:
            Base64-encoded image data if return_base64 is True, otherwise None
        """
        plt.figure(figsize=(14, 10))
        plt.title(title, fontsize=16)
        
        # Get position layout
        pos = nx.spring_layout(graph, k=0.4, iterations=100)
        
        # Draw edges
        nx.draw_networkx_edges(graph, pos, width=1, alpha=0.5, edge_color='gray')
        
        # Draw nodes with grouped colors
        for group, nodes in node_groups.items():
            if not nodes:
                continue
            nx.draw_networkx_nodes(graph, pos, nodelist=nodes,
                                 node_color=[node_colors[group]] * len(nodes),
                                 node_size=800, alpha=0.8, label=group)
        
        # Draw labels with service names
        labels = {node: data.get('name', node) for node, data in graph.nodes(data=True)}
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=9, 
                              font_family='sans-serif')
        
        plt.legend(loc='upper right', frameon=True, facecolor='white', edgecolor='gray',
                 bbox_to_anchor=(1.15, 1))
        
        plt.axis('off')  # Turn off the axis
        
        if return_base64:
            # Return as base64 string
            buf = BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
            buf.seek(0)
            img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            plt.close()
            return img_base64
        elif output_path:
            # Save to file
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            return None
"""
Service dependency visualization for Proxmox NLI.
Provides tools to visualize service dependencies and relationships.
"""
import logging
import os
from typing import Dict, List, Optional, Any, Set
import json
import networkx as nx
from datetime import datetime

logger = logging.getLogger(__name__)

class DependencyVisualizer:
    """Visualizes service dependencies and relationships."""
    
    def __init__(self, service_manager, output_dir=None):
        """Initialize the dependency visualizer.
        
        Args:
            service_manager: ServiceManager instance to interact with services
            output_dir: Directory to save visualization files (defaults to a subdirectory)
        """
        self.service_manager = service_manager
        
        # Set output directory
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(os.path.dirname(__file__), 'data', 'visualizations')
            
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_dependency_graph(self, include_undeployed=False) -> Dict[str, Any]:
        """Generate a dependency graph of all services.
        
        Args:
            include_undeployed: Whether to include undeployed services from the catalog
            
        Returns:
            Dictionary with graph data
        """
        # Get list of services
        deployed_services = self.service_manager.list_deployed_services()
        if not deployed_services.get("success"):
            return {
                "success": False,
                "message": "Failed to get deployed services",
                "graph": None
            }
            
        # Create graph
        graph = {
            "nodes": [],
            "edges": []
        }
        
        # Add deployed services to graph
        services = deployed_services.get("services", [])
        processed_service_ids = set()
        
        for service in services:
            service_id = service.get("service_id")
            if not service_id:
                continue
                
            # Add node for service
            graph["nodes"].append({
                "id": service_id,
                "label": service.get("name", service_id),
                "status": service.get("status", "unknown"),
                "type": "deployed",
                "vm_id": service.get("vm_id")
            })
            
            processed_service_ids.add(service_id)
            
            # Check dependencies in service definition
            service_def = self.service_manager.catalog.get_service(service_id)
            if not service_def:
                continue
                
            dependencies = service_def.get("dependencies", [])
            for dep in dependencies:
                # Add edge for dependency
                graph["edges"].append({
                    "source": service_id,
                    "target": dep,
                    "type": "depends_on"
                })
                
                # Make sure dependency is in the graph
                if dep not in processed_service_ids and include_undeployed:
                    dep_def = self.service_manager.catalog.get_service(dep)
                    if dep_def:
                        graph["nodes"].append({
                            "id": dep,
                            "label": dep_def.get("name", dep),
                            "status": "not_deployed",
                            "type": "catalog",
                            "vm_id": None
                        })
                        processed_service_ids.add(dep)
        
        # Find and add implicit dependencies (services deployed on same VM)
        vm_to_services = {}
        for service in services:
            vm_id = service.get("vm_id")
            service_id = service.get("service_id")
            if vm_id and service_id:
                if vm_id not in vm_to_services:
                    vm_to_services[vm_id] = []
                vm_to_services[vm_id].append(service_id)
        
        # Add implicit dependency edges for services on the same VM
        for vm_id, service_ids in vm_to_services.items():
            if len(service_ids) > 1:
                for i in range(len(service_ids)):
                    for j in range(i+1, len(service_ids)):
                        # Add bidirectional co-location edges
                        graph["edges"].append({
                            "source": service_ids[i],
                            "target": service_ids[j],
                            "type": "co_located"
                        })
                        graph["edges"].append({
                            "source": service_ids[j],
                            "target": service_ids[i],
                            "type": "co_located"
                        })
        
        # Save graph to file
        graph_path = os.path.join(self.output_dir, 'dependency_graph.json')
        try:
            with open(graph_path, 'w') as f:
                json.dump(graph, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving dependency graph: {str(e)}")
        
        return {
            "success": True,
            "graph": graph,
            "graph_path": graph_path,
            "services_count": len(processed_service_ids)
        }
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze service dependencies to find potential issues.
        
        Returns:
            Dictionary with analysis results
        """
        # Generate dependency graph first
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph["nodes"]:
            G.add_node(node["id"], **node)
            
        # Add edges
        for edge in graph["edges"]:
            if edge["type"] == "depends_on":  # Only consider actual dependencies
                G.add_edge(edge["source"], edge["target"], type=edge["type"])
        
        analysis = {
            "missing_dependencies": [],
            "circular_dependencies": [],
            "critical_services": [],
            "isolated_services": []
        }
        
        # Check for missing dependencies (dependencies that aren't deployed)
        deployed_service_ids = {n["id"] for n in graph["nodes"] if n["type"] == "deployed"}
        for edge in graph["edges"]:
            if edge["type"] == "depends_on" and edge["target"] not in deployed_service_ids:
                service_node = next((n for n in graph["nodes"] if n["id"] == edge["source"]), None)
                dependency_node = next((n for n in graph["nodes"] if n["id"] == edge["target"]), None)
                
                if service_node and dependency_node:
                    analysis["missing_dependencies"].append({
                        "service": service_node["label"],
                        "service_id": edge["source"],
                        "dependency": dependency_node["label"],
                        "dependency_id": edge["target"]
                    })
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(G))
            for cycle in cycles:
                if len(cycle) > 1:  # Ignore self-loops
                    cycle_services = []
                    for service_id in cycle:
                        service_node = next((n for n in graph["nodes"] if n["id"] == service_id), None)
                        if service_node:
                            cycle_services.append({
                                "name": service_node["label"],
                                "id": service_id
                            })
                    
                    analysis["circular_dependencies"].append({
                        "services": cycle_services,
                        "length": len(cycle)
                    })
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {str(e)}")
        
        # Find critical services (many dependents)
        in_degree = dict(G.in_degree())
        critical_threshold = 2  # Services with at least this many dependents
        for node_id, degree in in_degree.items():
            if degree >= critical_threshold:
                service_node = next((n for n in graph["nodes"] if n["id"] == node_id), None)
                if service_node:
                    dependents = [G.nodes[pred]["label"] for pred in G.predecessors(node_id)]
                    analysis["critical_services"].append({
                        "service": service_node["label"],
                        "service_id": node_id,
                        "dependents_count": degree,
                        "dependents": dependents
                    })
        
        # Find isolated services (no dependencies and not depended upon)
        for node in graph["nodes"]:
            if node["type"] == "deployed" and node["id"] not in G:
                analysis["isolated_services"].append({
                    "service": node["label"],
                    "service_id": node["id"]
                })
                
        return {
            "success": True,
            "analysis": analysis
        }
        
    def generate_dependency_report(self) -> Dict[str, Any]:
        """Generate a natural language report on service dependencies.
        
        Returns:
            Report dictionary with natural language dependency assessment
        """
        # Generate analysis first
        analysis_result = self.analyze_dependencies()
        if not analysis_result.get("success"):
            return {
                "success": False,
                "message": analysis_result.get("message", "Failed to analyze dependencies"),
                "report": "Unable to generate a dependency report at this time."
            }
            
        analysis = analysis_result["analysis"]
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        graph = graph_result.get("graph", {})
        nodes = graph.get("nodes", [])
        
        # Build report sections
        sections = []
        
        # Overview section
        deployed_count = len([n for n in nodes if n["type"] == "deployed"])
        total_count = len(nodes)
        
        overview = "## Service Dependency Report\n\n"
        overview += f"You have {deployed_count} deployed services"
        if total_count > deployed_count:
            overview += f" with {total_count - deployed_count} additional service dependencies from the catalog"
        overview += ".\n\n"
        
        sections.append(overview)
        
        # Missing dependencies section
        missing_deps = analysis.get("missing_dependencies", [])
        if missing_deps:
            missing_section = "### Missing Dependencies\n\n"
            missing_section += f"There {'is' if len(missing_deps) == 1 else 'are'} {len(missing_deps)} service{'s' if len(missing_deps) != 1 else ''} with missing dependencies:\n\n"
            
            for dep in missing_deps:
                missing_section += f"- **{dep['service']}** depends on **{dep['dependency']}**, which is not deployed\n"
                
            missing_section += "\nMissing dependencies may lead to service malfunctions. Consider deploying these dependencies.\n\n"
            sections.append(missing_section)
        
        # Circular dependencies section
        circular_deps = analysis.get("circular_dependencies", [])
        if circular_deps:
            circular_section = "### Circular Dependencies\n\n"
            circular_section += f"Found {len(circular_deps)} circular {'dependency' if len(circular_deps) == 1 else 'dependencies'}:\n\n"
            
            for i, cycle in enumerate(circular_deps, 1):
                cycle_names = [s['name'] for s in cycle['services']]
                circular_section += f"{i}. {' → '.join(cycle_names)} → {cycle_names[0]}\n"
                
            circular_section += "\nCircular dependencies can cause deployment issues and service failures. Consider refactoring your architecture.\n\n"
            sections.append(circular_section)
        
        # Critical services section
        critical_services = analysis.get("critical_services", [])
        if critical_services:
            critical_section = "### Critical Services\n\n"
            critical_section += f"Found {len(critical_services)} critical {'service' if len(critical_services) == 1 else 'services'} that other services depend on:\n\n"
            
            # Sort by number of dependents
            critical_services.sort(key=lambda s: s['dependents_count'], reverse=True)
            
            for service in critical_services:
                critical_section += f"- **{service['service']}** has {service['dependents_count']} {'dependent' if service['dependents_count'] == 1 else 'dependents'}"
                if len(service['dependents']) <= 3:
                    critical_section += f": {', '.join(service['dependents'])}"
                critical_section += "\n"
                
            critical_section += "\nThese services are critical to your infrastructure. Ensure they have proper monitoring and high availability.\n\n"
            sections.append(critical_section)
        
        # Isolated services section
        isolated_services = analysis.get("isolated_services", [])
        if isolated_services:
            isolated_section = "### Isolated Services\n\n"
            isolated_section += f"Found {len(isolated_services)} isolated {'service' if len(isolated_services) == 1 else 'services'} without dependencies:\n\n"
            
            for service in isolated_services:
                isolated_section += f"- **{service['service']}**\n"
                
            isolated_section += "\nThese services operate independently. They may be stand-alone applications or may need integration with other services.\n\n"
            sections.append(isolated_section)
            
        # Add recommendations section
        rec_section = "### Recommendations\n\n"
        recommendations = []
        
        if missing_deps:
            recommendations.append("Deploy missing dependencies to ensure proper service operation")
            
        if circular_deps:
            recommendations.append("Refactor services to eliminate circular dependencies")
            
        if critical_services:
            recommendations.append("Implement high availability for critical services")
            recommendations.append("Set up priority monitoring for services with many dependents")
            
        if isolated_services and len(isolated_services) > deployed_count / 2:
            recommendations.append("Consider integrating isolated services to improve system cohesion")
            
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                rec_section += f"{i}. {rec}\n"
        else:
            rec_section += "Your service dependencies look good! No specific recommendations at this time.\n"
            
        sections.append(rec_section)
        
        # Combine all sections
        full_report = '\n'.join(sections)
        
        return {
            "success": True,
            "report": full_report,
            "analysis": analysis
        }
    
    def generate_dot_graph(self, output_file=None) -> Dict[str, Any]:
        """Generate a DOT format graph for visualization with Graphviz.
        
        Args:
            output_file: Optional file path to save the DOT file (defaults to 'service_dependencies.dot')
            
        Returns:
            Dictionary with DOT format graph and file path
        """
        # Generate dependency graph first
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create DOT format graph
        dot_lines = ['digraph ServiceDependencies {']
        dot_lines.append('  rankdir="LR";')  # Left to right layout
        dot_lines.append('  node [shape=box, style=filled];')
        dot_lines.append('')
        
        # Add nodes with styling
        for node in graph["nodes"]:
            node_id = node["id"]
            label = node["label"]
            status = node["status"]
            node_type = node["type"]
            
            # Set node style based on type and status
            if node_type == "deployed":
                if status == "running" or "up" in status.lower():
                    fillcolor = "palegreen"
                elif "error" in status.lower() or "down" in status.lower() or status == "not running":
                    fillcolor = "lightcoral"
                else:
                    fillcolor = "lightyellow"
            else:
                fillcolor = "lightgray"  # Undeployed services
                
            dot_lines.append(f'  "{node_id}" [label="{label}", fillcolor="{fillcolor}"];')
            
        dot_lines.append('')
        
        # Add edges
        for edge in graph["edges"]:
            source = edge["source"]
            target = edge["target"]
            edge_type = edge["type"]
            
            # Style depends_on and co_located edges differently
            if edge_type == "depends_on":
                dot_lines.append(f'  "{source}" -> "{target}" [color="black", penwidth=1.0];')
            elif edge_type == "co_located":
                dot_lines.append(f'  "{source}" -> "{target}" [color="blue", style="dashed", dir=none, constraint=false];')
                
        # Close graph
        dot_lines.append('}')
        dot_content = '\n'.join(dot_lines)
        
        # Save DOT file
        if not output_file:
            output_file = os.path.join(self.output_dir, 'service_dependencies.dot')
            
        try:
            with open(output_file, 'w') as f:
                f.write(dot_content)
                
            return {
                "success": True,
                "dot_content": dot_content,
                "file_path": output_file,
                "message": f"DOT graph saved to {output_file}"
            }
        except Exception as e:
            logger.error(f"Error saving DOT graph: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving DOT graph: {str(e)}",
                "dot_content": dot_content
            }
    
    def generate_mermaid_graph(self, output_file=None) -> Dict[str, Any]:
        """Generate a Mermaid format graph for visualization.
        
        Args:
            output_file: Optional file path to save the Mermaid file (defaults to 'service_dependencies.mmd')
            
        Returns:
            Dictionary with Mermaid format graph and file path
        """
        # Generate dependency graph first
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create Mermaid format graph
        mmd_lines = ['graph TD']  # Top-down layout
        
        # Add nodes with styling
        for node in graph["nodes"]:
            node_id = node["id"].replace("-", "_")  # Mermaid has issues with hyphens in IDs
            label = node["label"]
            status = node["status"]
            node_type = node["type"]
            
            # Set node style based on type and status
            if node_type == "deployed":
                if status == "running" or "up" in status.lower():
                    style = "fill:#d0f0c0"  # Light green
                elif "error" in status.lower() or "down" in status.lower() or status == "not running":
                    style = "fill:#ffcccb"  # Light red
                else:
                    style = "fill:#ffffcc"  # Light yellow
            else:
                style = "fill:#f0f0f0"  # Light gray for undeployed
                
            mmd_lines.append(f'    {node_id}["{label}"]:::{"deployed" if node_type == "deployed" else "undeployed"} style "{style}"')
            
        # Add class definitions
        mmd_lines.append('    classDef deployed stroke:#009900,stroke-width:2px')
        mmd_lines.append('    classDef undeployed stroke:#999999,stroke-width:1px,stroke-dasharray: 5 5')
        
        # Add edges
        for edge in graph["edges"]:
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            edge_type = edge["type"]
            
            if edge_type == "depends_on":
                mmd_lines.append(f'    {source} --> {target}')
            elif edge_type == "co_located":
                mmd_lines.append(f'    {source} -.- {target}')
                
        mmd_content = '\n'.join(mmd_lines)
        
        # Save Mermaid file
        if not output_file:
            output_file = os.path.join(self.output_dir, 'service_dependencies.mmd')
            
        try:
            with open(output_file, 'w') as f:
                f.write(mmd_content)
                
            return {
                "success": True,
                "mermaid_content": mmd_content,
                "file_path": output_file,
                "message": f"Mermaid graph saved to {output_file}"
            }
        except Exception as e:
            logger.error(f"Error saving Mermaid graph: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving Mermaid graph: {str(e)}",
                "mermaid_content": mmd_content
            }
    
    def generate_interactive_visualization(self, include_undeployed=False) -> Dict[str, Any]:
        """Generate an interactive visualization of service dependencies.
        
        Args:
            include_undeployed: Whether to include undeployed services from the catalog
            
        Returns:
            Dictionary with visualization data
        """
        # First generate the dependency graph
        graph_result = self.generate_dependency_graph(include_undeployed)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create HTML visualization using D3.js
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Service Dependency Visualization</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }
                #visualization {
                    width: 100%;
                    height: 100vh;
                    background-color: white;
                }
                .node {
                    cursor: pointer;
                }
                .link {
                    stroke-width: 2px;
                }
                .node text {
                    font-size: 12px;
                    fill: #333;
                }
                .tooltip {
                    position: absolute;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    pointer-events: none;
                    font-size: 14px;
                    max-width: 300px;
                }
                .controls {
                    position: absolute;
                    top: 10px;
                    left: 10px;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .legend {
                    position: absolute;
                    bottom: 10px;
                    left: 10px;
                    padding: 10px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                .legend-item {
                    display: flex;
                    align-items: center;
                    margin-bottom: 5px;
                }
                .legend-color {
                    width: 20px;
                    height: 20px;
                    margin-right: 10px;
                    border-radius: 3px;
                }
            </style>
        </head>
        <body>
            <div id="visualization"></div>
            <div class="controls">
                <button id="zoom-in">Zoom In</button>
                <button id="zoom-out">Zoom Out</button>
                <button id="reset">Reset</button>
                <label><input type="checkbox" id="show-labels" checked> Show Labels</label>
            </div>
            <div class="legend">
                <h3>Legend</h3>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #4CAF50;"></div>
                    <div>Running Service</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #F44336;"></div>
                    <div>Stopped Service</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #9E9E9E;"></div>
                    <div>Not Deployed</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #2196F3;"></div>
                    <div>Restarting</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FF9800;"></div>
                    <div>Warning</div>
                </div>
                <hr>
                <div class="legend-item">
                    <svg width="50" height="10">
                        <line x1="0" y1="5" x2="50" y2="5" stroke="#333" stroke-width="2"></line>
                    </svg>
                    <div>Depends On</div>
                </div>
                <div class="legend-item">
                    <svg width="50" height="10">
                        <line x1="0" y1="5" x2="50" y2="5" stroke="#999" stroke-width="2" stroke-dasharray="5,5"></line>
                    </svg>
                    <div>Co-located</div>
                </div>
            </div>
            <div id="tooltip" class="tooltip" style="display: none;"></div>
            
            <script>
            // Graph data from Python
            const graphData = {
                nodes: JSON.parse('${nodes}'),
                edges: JSON.parse('${edges}')
            };
            
            // Set up the visualization
            const width = window.innerWidth;
            const height = window.innerHeight;
            
            // Create SVG
            const svg = d3.select("#visualization")
                .append("svg")
                .attr("width", width)
                .attr("height", height);
                
            // Create zoom behavior
            const zoom = d3.zoom()
                .scaleExtent([0.1, 4])
                .on("zoom", (event) => {
                    g.attr("transform", event.transform);
                });
                
            svg.call(zoom);
            
            // Create main group for zoom
            const g = svg.append("g");
            
            // Create tooltip
            const tooltip = d3.select("#tooltip");
            
            // Create links
            const link = g.append("g")
                .selectAll("line")
                .data(graphData.edges)
                .enter()
                .append("line")
                .attr("class", "link")
                .attr("stroke", d => d.type === "depends_on" ? "#333" : "#999")
                .attr("stroke-dasharray", d => d.type === "depends_on" ? null : "5,5");
            
            // Create nodes
            const node = g.append("g")
                .selectAll("g")
                .data(graphData.nodes)
                .enter()
                .append("g")
                .attr("class", "node")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            // Add circles to nodes
            node.append("circle")
                .attr("r", 15)
                .attr("fill", d => {
                    if (d.status === "Running" || d.status.includes("Up")) return "#4CAF50";
                    if (d.status === "Stopped" || d.status.includes("Exited")) return "#F44336";
                    if (d.status === "not_deployed") return "#9E9E9E";
                    if (d.status.includes("Restarting")) return "#2196F3";
                    return "#FF9800"; // Warning/Unknown
                })
                .attr("stroke", "#fff")
                .attr("stroke-width", 2)
                .on("mouseover", showTooltip)
                .on("mouseout", hideTooltip);
            
            // Add labels to nodes
            const labels = node.append("text")
                .text(d => d.label)
                .attr("x", 20)
                .attr("y", 5)
                .attr("text-anchor", "start");
            
            // Set up force simulation
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.edges)
                    .id(d => d.id)
                    .distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .force("collide", d3.forceCollide().radius(50))
                .on("tick", ticked);
            
            // Update positions on tick
            function ticked() {
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("transform", d => `translate(${d.x},${d.y})`);
            }
            
            // Drag functions
            function dragstarted(event, d) {
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }
            
            function dragged(event, d) {
                d.fx = event.x;
                d.fy = event.y;
            }
            
            function dragended(event, d) {
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }
            
            // Tooltip functions
            function showTooltip(event, d) {
                const content = `
                    <strong>${d.label}</strong><br>
                    Status: ${d.status}<br>
                    ${d.vm_id ? `VM ID: ${d.vm_id}<br>` : ''}
                    Type: ${d.type === 'deployed' ? 'Deployed Service' : 'Catalog Service'}<br>
                `;
                
                tooltip.html(content)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY + 10) + "px")
                    .style("display", "block");
            }
            
            function hideTooltip() {
                tooltip.style("display", "none");
            }
            
            // Controls
            d3.select("#zoom-in").on("click", () => {
                svg.transition().call(zoom.scaleBy, 1.2);
            });
            
            d3.select("#zoom-out").on("click", () => {
                svg.transition().call(zoom.scaleBy, 0.8);
            });
            
            d3.select("#reset").on("click", () => {
                svg.transition().call(zoom.transform, d3.zoomIdentity);
            });
            
            d3.select("#show-labels").on("change", function() {
                const showLabels = this.checked;
                labels.style("display", showLabels ? "block" : "none");
            });
            </script>
        </body>
        </html>
        """
        
        # Replace placeholders with actual data
        html = html.replace("${nodes}", json.dumps(graph["nodes"]))
        html = html.replace("${edges}", json.dumps(graph["edges"]))
        
        # Save HTML to file
        html_path = os.path.join(self.output_dir, 'dependency_visualization.html')
        try:
            with open(html_path, 'w') as f:
                f.write(html)
        except Exception as e:
            logger.error(f"Error saving visualization HTML: {str(e)}")
            return {
                "success": False,
                "message": f"Error saving visualization: {str(e)}"
            }
        
        return {
            "success": True,
            "message": "Successfully generated interactive visualization",
            "visualization_path": html_path,
            "services_count": len(graph["nodes"])
        }
    
    def generate_natural_language_description(self, service_id: str = None) -> Dict[str, Any]:
        """Generate a natural language description of service dependencies.
        
        Args:
            service_id: Optional service ID to focus on. If None, describes all services.
            
        Returns:
            Dictionary with natural language description
        """
        # First generate the dependency graph
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph["nodes"]:
            G.add_node(node["id"], **node)
            
        # Add edges
        for edge in graph["edges"]:
            if edge["type"] == "depends_on":  # Only consider actual dependencies
                G.add_edge(edge["source"], edge["target"], type=edge["type"])
        
        # Generate description
        if service_id:
            # Focus on a specific service
            if service_id not in G:
                return {
                    "success": False,
                    "message": f"Service '{service_id}' not found in dependency graph"
                }
                
            # Get service node
            service_node = G.nodes[service_id]
            service_name = service_node.get("label", service_id)
            
            # Get dependencies (outgoing edges)
            dependencies = list(G.successors(service_id))
            
            # Get dependents (incoming edges)
            dependents = list(G.predecessors(service_id))
            
            # Generate description
            description = f"## Dependency Analysis for {service_name}\n\n"
            
            # Describe dependencies
            if dependencies:
                description += f"{service_name} depends on {len(dependencies)} service{'s' if len(dependencies) > 1 else ''}:\n\n"
                for dep_id in dependencies:
                    dep_node = G.nodes[dep_id]
                    dep_name = dep_node.get("label", dep_id)
                    dep_status = dep_node.get("status", "unknown")
                    
                    # Check if dependency is deployed
                    if dep_status == "not_deployed":
                        description += f"- {dep_name} (NOT DEPLOYED - this may cause issues)\n"
                    elif "Up" in dep_status or "Running" in dep_status:
                        description += f"- {dep_name} (running)\n"
                    elif "Exited" in dep_status or "Stopped" in dep_status:
                        description += f"- {dep_name} (stopped - this may cause issues)\n"
                    else:
                        description += f"- {dep_name} (status: {dep_status})\n"
            else:
                description += f"{service_name} does not depend on any other services.\n\n"
            
            # Describe dependents
            if dependents:
                description += f"\n{len(dependents)} service{'s' if len(dependents) > 1 else ''} depend{'s' if len(dependents) == 1 else ''} on {service_name}:\n\n"
                for dep_id in dependents:
                    dep_node = G.nodes[dep_id]
                    dep_name = dep_node.get("label", dep_id)
                    dep_status = dep_node.get("status", "unknown")
                    
                    if "Up" in dep_status or "Running" in dep_status:
                        description += f"- {dep_name} (running)\n"
                    elif "Exited" in dep_status or "Stopped" in dep_status:
                        description += f"- {dep_name} (stopped)\n"
                    else:
                        description += f"- {dep_name} (status: {dep_status})\n"
            else:
                description += f"\nNo other services depend on {service_name}.\n"
                
            # Add impact analysis
            description += f"\n## Impact Analysis\n\n"
            
            if dependents:
                description += f"If {service_name} goes down, it would affect {len(dependents)} other service{'s' if len(dependents) > 1 else ''}.\n"
                
                # Find all indirect dependents (transitive closure)
                all_dependents = set()
                for dep in dependents:
                    all_dependents.add(dep)
                    all_dependents.update(nx.descendants(G, dep))
                
                indirect_dependents = all_dependents - set(dependents)
                if indirect_dependents:
                    description += f"Additionally, {len(indirect_dependents)} service{'s' if len(indirect_dependents) > 1 else ''} would be indirectly affected:\n\n"
                    for dep_id in indirect_dependents:
                        dep_node = G.nodes[dep_id]
                        dep_name = dep_node.get("label", dep_id)
                        description += f"- {dep_name}\n"
            else:
                description += f"If {service_name} goes down, no other services would be directly affected.\n"
                
            # Add recommendations
            description += f"\n## Recommendations\n\n"
            
            missing_deps = [G.nodes[dep_id] for dep_id in dependencies if G.nodes[dep_id].get("status") == "not_deployed"]
            stopped_deps = [G.nodes[dep_id] for dep_id in dependencies if "Exited" in G.nodes[dep_id].get("status", "") or "Stopped" in G.nodes[dep_id].get("status", "")]
            
            if missing_deps:
                description += "- Consider deploying these missing dependencies:\n"
                for dep in missing_deps:
                    description += f"  - {dep.get('label', dep['id'])}\n"
                    
            if stopped_deps:
                description += "- Start these stopped dependencies:\n"
                for dep in stopped_deps:
                    description += f"  - {dep.get('label', dep['id'])}\n"
                    
            if dependents and dependencies:
                description += f"- {service_name} is a critical service with both dependencies and dependents.\n"
                description += "  Consider implementing high availability for this service.\n"
                
        else:
            # Describe the entire dependency graph
            description = "# Service Dependency Overview\n\n"
            
            # Count services by status
            status_counts = {}
            for node in graph["nodes"]:
                status = node.get("status", "unknown")
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
                
            # Summarize services
            description += f"There are {len(graph['nodes'])} services in the dependency graph:\n\n"
            for status, count in status_counts.items():
                description += f"- {count} service{'s' if count > 1 else ''} with status: {status}\n"
                
            # Find critical services (high degree centrality)
            centrality = nx.degree_centrality(G)
            critical_services = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            
            if critical_services:
                description += "\n## Critical Services\n\n"
                description += "These services have the most dependencies or dependents:\n\n"
                
                for service_id, score in critical_services:
                    if score > 0:
                        service_node = G.nodes[service_id]
                        service_name = service_node.get("label", service_id)
                        in_degree = G.in_degree(service_id)  # Number of dependents
                        out_degree = G.out_degree(service_id)  # Number of dependencies
                        
                        description += f"- {service_name}: {in_degree} dependent{'s' if in_degree != 1 else ''}, {out_degree} dependenc{'ies' if out_degree != 1 else 'y'}\n"
            
            # Find isolated services (no dependencies or dependents)
            isolated = [n for n, d in G.degree() if d == 0]
            if isolated:
                description += "\n## Isolated Services\n\n"
                description += "These services have no dependencies or dependents:\n\n"
                
                for service_id in isolated:
                    service_node = G.nodes[service_id]
                    service_name = service_node.get("label", service_id)
                    description += f"- {service_name}\n"
                    
            # Find circular dependencies
            try:
                cycles = list(nx.simple_cycles(G))
                if cycles:
                    description += "\n## Circular Dependencies\n\n"
                    description += "These circular dependencies might cause issues:\n\n"
                    
                    for i, cycle in enumerate(cycles[:5]):  # Show at most 5 cycles
                        cycle_desc = " → ".join([G.nodes[n].get("label", n) for n in cycle])
                        description += f"{i+1}. {cycle_desc} → (repeats)\n"
                        
                    if len(cycles) > 5:
                        description += f"...and {len(cycles) - 5} more circular dependencies\n"
            except Exception as e:
                logger.error(f"Error finding cycles: {str(e)}")
                
            # Add recommendations
            description += "\n## Recommendations\n\n"
            
            # Find missing dependencies
            missing_deps = [(src, tgt) for src, tgt, data in G.edges(data=True) 
                           if G.nodes[tgt].get("status") == "not_deployed"]
            
            if missing_deps:
                description += "- Deploy these missing dependencies:\n"
                for src, tgt in missing_deps[:5]:  # Show at most 5
                    src_name = G.nodes[src].get("label", src)
                    tgt_name = G.nodes[tgt].get("label", tgt)
                    description += f"  - {tgt_name} (needed by {src_name})\n"
                    
                if len(missing_deps) > 5:
                    description += f"  - ...and {len(missing_deps) - 5} more\n"
                    
            if critical_services:
                description += "- Consider implementing high availability for critical services\n"
                
            if isolated:
                description += "- Review isolated services to determine if they should be integrated with other services\n"
                
            if cycles:
                description += "- Resolve circular dependencies to prevent potential issues\n"
        
        return {
            "success": True,
            "description": description,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_service_impact(self, service_id: str) -> Dict[str, Any]:
        """Analyze the impact of a service failure.
        
        Args:
            service_id: ID of the service to analyze impact for
            
        Returns:
            Dictionary with impact analysis
        """
        # Generate dependency graph first
        graph_result = self.generate_dependency_graph(include_undeployed=True)
        if not graph_result.get("success"):
            return graph_result
            
        graph = graph_result["graph"]
        
        # Create NetworkX graph for analysis
        G = nx.DiGraph()
        
        # Add nodes
        for node in graph["nodes"]:
            G.add_node(node["id"], **node)
            
        # Add edges (reversed direction to find dependents)
        for edge in graph["edges"]:
            if edge["type"] == "depends_on":
                G.add_edge(edge["target"], edge["source"], type=edge["type"])
        
        # Check if service exists in graph
        if service_id not in G:
            return {
                "success": False,
                "message": f"Service '{service_id}' not found in dependency graph",
                "impact": None
            }
        
        # Find all dependents (direct and indirect)
        try:
            descendants = nx.descendants(G, service_id)
            descendants = list(descendants)
        except Exception as e:
            logger.error(f"Error finding service dependents: {str(e)}")
            descendants = []
            
        # If service has no dependents
        if not descendants:
            return {
                "success": True,
                "impacted_services": [],
                "impact_level": "none",
                "message": f"Service '{service_id}' has no dependents. If it fails, no other services will be affected."
            }
            
        # Get details of impacted services
        impacted_services = []
        for desc_id in descendants:
            node = G.nodes[desc_id]
            impacted_services.append({
                "id": desc_id,
                "name": node.get("label", desc_id),
                "status": node.get("status", "unknown"),
                "type": node.get("type", "unknown")
            })
            
        # Determine impact level based on number of dependents
        if len(impacted_services) > 3:
            impact_level = "critical"
        elif len(impacted_services) > 1:
            impact_level = "significant" 
        else:
            impact_level = "minimal"
            
        return {
            "success": True,
            "service_id": service_id,
            "service_name": next((n["label"] for n in graph["nodes"] if n["id"] == service_id), service_id),
            "impacted_services": impacted_services,
            "impact_count": len(impacted_services),
            "impact_level": impact_level
        }
        
    def generate_impact_report(self, service_id: str) -> Dict[str, Any]:
        """Generate a natural language report on the impact of a service failure.
        
        Args:
            service_id: ID of the service to analyze impact for
            
        Returns:
            Dictionary with natural language impact report
        """
        # Get impact analysis
        impact_result = self.get_service_impact(service_id)
        if not impact_result.get("success"):
            return {
                "success": False,
                "message": impact_result.get("message", f"Failed to analyze impact for '{service_id}'"),
                "report": f"Unable to generate an impact report for {service_id}."
            }
            
        service_name = impact_result["service_name"]
        impacted_services = impact_result["impacted_services"]
        impact_level = impact_result["impact_level"]
        
        # Build report
        report = f"## Service Impact Analysis: {service_name}\n\n"
        
        if not impacted_services:
            report += f"The {service_name} service does not have any dependents. If it fails, no other services will be directly affected.\n\n"
            report += "This service can be safely restarted or maintained without disrupting other services."
        else:
            report += f"If the {service_name} service fails, it will impact {len(impacted_services)} other {'service' if len(impacted_services) == 1 else 'services'}.\n\n"
            
            # Add impact level description
            if impact_level == "critical":
                report += f"**Impact Level: Critical** - A failure of {service_name} would have widespread effects on your infrastructure.\n\n"
            elif impact_level == "significant":
                report += f"**Impact Level: Significant** - Multiple services depend on {service_name} and would be affected by its failure.\n\n"
            else:
                report += f"**Impact Level: Minimal** - Only a small number of services would be affected.\n\n"
                
            # List affected services
            report += "### Affected Services\n\n"
            for service in impacted_services:
                report += f"- **{service['name']}** ({service['status']})\n"
                
            # Add recommendations
            report += "\n### Recommendations\n\n"
            
            if impact_level == "critical":
                report += "1. Implement high availability for this critical service\n"
                report += "2. Schedule maintenance during low-usage periods\n"
                report += "3. Develop a failure mitigation plan\n"
                report += "4. Consider redesigning dependencies to reduce the impact of failure\n"
            elif impact_level == "significant":
                report += "1. Monitor this service closely\n"
                report += "2. Schedule maintenance carefully\n"
                report += "3. Test failure scenarios to ensure proper recovery\n"
            else:
                report += "1. Standard maintenance procedures should be sufficient\n"
                report += "2. Notify the owners of affected services before performing maintenance\n"
            
        return {
            "success": True,
            "report": report,
            "impact": impact_result
        }
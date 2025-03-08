/**
 * Network diagram visualization for Proxmox NLI
 * Uses D3.js to create an interactive visualization of VMs, containers, and services
 */
class NetworkDiagram {
    constructor(containerId) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.width = this.container.clientWidth;
        this.height = 400;
        this.nodes = [];
        this.links = [];
        this.simulation = null;
        this.svg = null;
        this.linkElements = null;
        this.nodeElements = null;
        this.textElements = null;
        this.tooltipDiv = null;
        
        // Node types with their colors
        this.nodeTypes = {
            'node': '#6c757d',       // Physical nodes (gray)
            'vm': '#0d6efd',         // VMs (blue)
            'ct': '#198754',         // Containers (green)
            'service': '#ffc107',    // Services (yellow)
            'storage': '#dc3545',    // Storage (red)
            'network': '#6610f2'     // Network components (purple)
        };
        
        this.initialize();
    }
    
    initialize() {
        // Create SVG container
        this.svg = d3.select(`#${this.containerId}`)
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('class', 'network-diagram');
            
        // Add zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.5, 4])
            .on('zoom', (event) => {
                this.svg.selectAll('g').attr('transform', event.transform);
            });
            
        this.svg.call(zoom);
        
        // Create a group for all elements
        this.g = this.svg.append('g');
        
        // Create tooltip div
        this.tooltipDiv = d3.select('body')
            .append('div')
            .attr('class', 'network-tooltip')
            .style('opacity', 0);
            
        // Initialize the force simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(40));
    }
    
    update(nodes, links) {
        this.nodes = nodes;
        this.links = links;
        
        // Update the links
        this.linkElements = this.g.selectAll('line')
            .data(this.links, d => `${d.source}-${d.target}`);
            
        this.linkElements.exit().remove();
        
        const linkEnter = this.linkElements
            .enter()
            .append('line')
            .attr('stroke-width', d => d.value)
            .attr('stroke', '#999')
            .attr('stroke-opacity', 0.6);
            
        this.linkElements = linkEnter.merge(this.linkElements);
        
        // Update the nodes
        this.nodeElements = this.g.selectAll('.node')
            .data(this.nodes, d => d.id);
            
        this.nodeElements.exit().remove();
        
        const nodeEnter = this.nodeElements
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', this.dragStarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragEnded.bind(this)));
                
        // Add circles for nodes
        nodeEnter
            .append('circle')
            .attr('r', d => d.type === 'node' ? 15 : 10)
            .attr('fill', d => this.nodeTypes[d.type] || '#777')
            .on('mouseover', (event, d) => {
                this.tooltipDiv.transition()
                    .duration(200)
                    .style('opacity', .9);
                    
                let tooltipContent = `<strong>${d.name}</strong><br>`;
                tooltipContent += `Type: ${d.type}<br>`;
                
                if (d.status) {
                    tooltipContent += `Status: ${d.status}<br>`;
                }
                
                if (d.details) {
                    Object.keys(d.details).forEach(key => {
                        tooltipContent += `${key}: ${d.details[key]}<br>`;
                    });
                }
                
                this.tooltipDiv.html(tooltipContent)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 28) + 'px');
            })
            .on('mouseout', () => {
                this.tooltipDiv.transition()
                    .duration(500)
                    .style('opacity', 0);
            })
            .on('click', (event, d) => {
                // Highlight connections
                this.highlightConnections(d);
                
                // Emit click event for integration with other components
                const clickEvent = new CustomEvent('node-click', {
                    detail: { node: d }
                });
                document.dispatchEvent(clickEvent);
            });
            
        // Add icons based on node type
        nodeEnter
            .append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('class', 'node-icon')
            .text(d => {
                switch (d.type) {
                    case 'node': return '🖥️';
                    case 'vm': return '💻';
                    case 'ct': return '📦';
                    case 'service': return '🚀';
                    case 'storage': return '💾';
                    case 'network': return '🌐';
                    default: return '❓';
                }
            });
            
        // Add text labels
        nodeEnter
            .append('text')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('y', 25)
            .attr('class', 'node-label')
            .text(d => d.name);
            
        this.nodeElements = nodeEnter.merge(this.nodeElements);
        
        // Update and restart the simulation
        this.simulation
            .nodes(this.nodes)
            .on('tick', this.ticked.bind(this));
            
        this.simulation.force('link').links(this.links);
        this.simulation.alpha(1).restart();
    }
    
    ticked() {
        // Update link positions
        this.linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
            
        // Update node positions
        this.nodeElements.attr('transform', d => `translate(${d.x}, ${d.y})`);
    }
    
    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    highlightConnections(node) {
        // Reset all nodes and links to default opacity
        this.svg.selectAll('line').attr('stroke-opacity', 0.6);
        this.svg.selectAll('.node').attr('opacity', 1);
        
        // Find connected nodes and links
        const connectedLinks = this.links.filter(link => 
            link.source.id === node.id || link.target.id === node.id
        );
        
        const connectedNodeIds = new Set();
        connectedNodeIds.add(node.id);
        
        connectedLinks.forEach(link => {
            connectedNodeIds.add(link.source.id);
            connectedNodeIds.add(link.target.id);
        });
        
        // Highlight connected nodes and links
        this.svg.selectAll('line')
            .attr('stroke-opacity', link => 
                link.source.id === node.id || link.target.id === node.id ? 1 : 0.1
            )
            .attr('stroke-width', link => 
                link.source.id === node.id || link.target.id === node.id ? link.value * 1.5 : link.value
            );
            
        this.svg.selectAll('.node')
            .attr('opacity', d => connectedNodeIds.has(d.id) ? 1 : 0.3);
    }
    
    resetHighlighting() {
        this.svg.selectAll('line')
            .attr('stroke-opacity', 0.6)
            .attr('stroke-width', d => d.value);
        
        this.svg.selectAll('.node')
            .attr('opacity', 1);
    }
    
    resize() {
        this.width = this.container.clientWidth;
        this.svg.attr('width', this.width);
        this.simulation.force('center', d3.forceCenter(this.width / 2, this.height / 2));
        this.simulation.alpha(1).restart();
    }
}
import React, { useEffect, useRef, useState } from 'react';
// import * as d3 from 'd3'; // Using CDN
const d3 = window.d3;

const ForceGraph = ({ nodes, links, myStockCodes }) => {
    const svgRef = useRef(null);
    const containerRef = useRef(null);
    const simulationRef = useRef(null);
    const nodePositionsRef = useRef({});  // Cache node positions

    useEffect(() => {
        if (!nodes.length || !svgRef.current || !containerRef.current) return;

        const svg = d3.select(svgRef.current);
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;

        // Clone data to avoid mutating props
        const nodesData = nodes.map(d => {
            // Restore cached position if exists
            const cached = nodePositionsRef.current[d.id];
            return {
                ...d,
                x: cached?.x || width / 2 + (Math.random() - 0.5) * 100,
                y: cached?.y || height / 2 + (Math.random() - 0.5) * 100,
                fx: cached?.fx || null,
                fy: cached?.fy || null
            };
        });
        const linksData = links.map(d => ({ ...d }));

        // Identify node types for styling
        nodesData.forEach(node => {
            if (myStockCodes.includes(node.id)) {
                node.type = 'my-stock';
                node.radius = 30;
                node.color = '#007AFF'; // Blue for my stocks
            } else {
                // Check if it's directly connected to my stock
                const isRelated = linksData.some(link =>
                    (link.source === node.id && myStockCodes.includes(link.target)) ||
                    (link.target === node.id && myStockCodes.includes(link.source)) ||
                    (link.source?.id === node.id && myStockCodes.includes(link.target?.id)) ||
                    (link.target?.id === node.id && myStockCodes.includes(link.source?.id))
                );

                if (isRelated) {
                    node.type = 'related';
                    node.radius = 20;
                    node.color = '#34C759'; // Green for related
                } else {
                    node.type = 'other';
                    node.radius = 10;
                    node.color = '#D1D1D6'; // Gray for others
                }
            }
        });

        // Stop previous simulation if exists
        if (simulationRef.current) {
            simulationRef.current.stop();
        }

        // Clear and rebuild SVG
        svg.selectAll("*").remove();

        // Simulation setup with lower alpha for stability
        const simulation = d3.forceSimulation(nodesData)
            .force("link", d3.forceLink(linksData).id(d => d.id).distance(100).strength(0.3))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2).strength(0.05))
            .force("collide", d3.forceCollide().radius(d => d.radius + 10))
            .alpha(0.3)  // Start with lower alpha for smoother movement
            .alphaDecay(0.02);  // Slow decay for stability

        simulationRef.current = simulation;

        // Draw links
        const link = svg.append("g")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .selectAll("line")
            .data(linksData)
            .join("line")
            .attr("stroke-width", d => Math.sqrt(d.value) * 3);

        // Draw nodes
        const node = svg.append("g")
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .selectAll("circle")
            .data(nodesData)
            .join("circle")
            .attr("r", d => d.radius)
            .attr("fill", d => d.color)
            .call(drag(simulation));

        // Add labels
        const labels = svg.append("g")
            .attr("class", "labels")
            .selectAll("text")
            .data(nodesData)
            .join("text")
            .attr("text-anchor", "middle")
            .attr("dy", d => -d.radius - 5)
            .text(d => d.name)
            .attr("font-size", d => d.type === 'my-stock' ? "14px" : "12px")
            .attr("font-weight", d => d.type === 'my-stock' ? "bold" : "normal")
            .attr("fill", "#333")
            .style("pointer-events", "none");

        // Update positions on each tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);

            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        });

        // Cache positions when simulation ends
        simulation.on("end", () => {
            nodesData.forEach(n => {
                nodePositionsRef.current[n.id] = { x: n.x, y: n.y, fx: n.fx, fy: n.fy };
            });
        });

        // Drag functions
        function drag(simulation) {
            function dragstarted(event) {
                if (!event.active) simulation.alphaTarget(0.1).restart();
                event.subject.fx = event.subject.x;
                event.subject.fy = event.subject.y;
            }

            function dragged(event) {
                event.subject.fx = event.x;
                event.subject.fy = event.y;
            }

            function dragended(event) {
                if (!event.active) simulation.alphaTarget(0);
                // Keep the node fixed after drag
                // event.subject.fx = null;  // Comment out to keep position
                // event.subject.fy = null;
                // Cache the new position
                nodePositionsRef.current[event.subject.id] = {
                    x: event.subject.x,
                    y: event.subject.y,
                    fx: event.subject.fx,
                    fy: event.subject.fy
                };
            }

            return d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended);
        }

        // Cleanup
        return () => {
            simulation.stop();
        };
    }, [nodes, links, myStockCodes]);

    return (
        <div ref={containerRef} style={{ width: '100%', height: '100%' }}>
            <svg ref={svgRef} width="100%" height="100%"></svg>
        </div>
    );
};

export default ForceGraph;

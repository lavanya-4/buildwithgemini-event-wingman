import React, { useEffect, useRef, useState } from 'react';
import { GraphData, GraphNode, GraphLink } from '../types';
import { RefreshCw, Users, Info, X } from 'lucide-react';

interface RelationshipGraphProps {
  graphData: GraphData;
  onRefresh: () => void;
  isLoading: boolean;
}

export const RelationshipGraph: React.FC<RelationshipGraphProps> = ({
  graphData,
  onRefresh,
  isLoading,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [links, setLinks] = useState<GraphLink[]>([]);

  // Simulation physics state
  useEffect(() => {
    if (!graphData || !graphData.nodes.length) {
      setNodes([]);
      setLinks([]);
      return;
    }

    const canvas = canvasRef.current;
    const width = canvas ? canvas.width : 600;
    const height = canvas ? canvas.height : 450;
    const centerX = width / 2;
    const centerY = height / 2;

    // Initialize node positions in circular layout around center
    const initializedNodes: GraphNode[] = graphData.nodes.map((node, i) => {
      const angle = (i / graphData.nodes.length) * 2 * Math.PI;
      const radius = node.type === 'me' ? 0 : 100 + (i % 3) * 50;
      return {
        ...node,
        x: centerX + Math.cos(angle) * radius + (Math.random() - 0.5) * 30,
        y: centerY + Math.sin(angle) * radius + (Math.random() - 0.5) * 30,
        vx: 0,
        vy: 0,
      };
    });

    setNodes(initializedNodes);
    setLinks(graphData.links);
  }, [graphData]);

  // Force-directed simulation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !nodes.length) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    const tick = () => {
      // 1. Repulsion between nodes
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i];
          const b = nodes[j];
          const dx = (b.x || 0) - (a.x || 0);
          const dy = (b.y || 0) - (a.y || 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 180) {
            const force = (180 - dist) / 180;
            const fx = (dx / dist) * force * 1.5;
            const fy = (dy / dist) * force * 1.5;
            a.vx = (a.vx || 0) - fx;
            a.vy = (a.vy || 0) - fy;
            b.vx = (b.vx || 0) + fx;
            b.vy = (b.vy || 0) + fy;
          }
        }
      }

      // 2. Spring attraction along links
      const nodeMap = new Map(nodes.map((n) => [n.id, n]));
      for (const link of links) {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (source && target) {
          const dx = (target.x || 0) - (source.x || 0);
          const dy = (target.y || 0) - (source.y || 0);
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const desiredDist = 110;
          const force = (dist - desiredDist) * 0.04;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;
          source.vx = (source.vx || 0) + fx;
          source.vy = (source.vy || 0) + fy;
          target.vx = (target.vx || 0) - fx;
          target.vy = (target.vy || 0) - fy;
        }
      }

      // 3. Gravity towards center & friction damping
      for (const node of nodes) {
        if (node.type === 'me') {
          node.x = centerX;
          node.y = centerY;
          continue;
        }
        const dx = centerX - (node.x || 0);
        const dy = centerY - (node.y || 0);
        node.vx = ((node.vx || 0) + dx * 0.005) * 0.88;
        node.vy = ((node.vy || 0) + dy * 0.005) * 0.88;
        node.x = Math.max(30, Math.min(width - 30, (node.x || 0) + node.vx));
        node.y = Math.max(30, Math.min(height - 30, (node.y || 0) + node.vy));
      }

      // 4. Render canvas
      ctx.clearRect(0, 0, width, height);

      // Render links
      for (const link of links) {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (source && target && source.x && source.y && target.x && target.y) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.strokeStyle = link.color || 'rgba(100, 116, 139, 0.35)';
          ctx.lineWidth = link.label === 'shared_topic' ? 2 : 1.2;
          ctx.stroke();

          // Optional link label for shared topics
          if (link.label === 'shared_topic') {
            const midX = (source.x + target.x) / 2;
            const midY = (source.y + target.y) / 2;
            ctx.fillStyle = 'rgba(16, 185, 129, 0.8)';
            ctx.font = '9px Plus Jakarta Sans';
            ctx.fillText('shared', midX - 12, midY);
          }
        }
      }

      // Render nodes
      for (const node of nodes) {
        if (!node.x || !node.y) continue;
        const radius = node.size || 14;

        // Glow ring for selected or me
        if (selectedNode?.id === node.id || node.type === 'me') {
          ctx.beginPath();
          ctx.arc(node.x, node.y, radius + 6, 0, 2 * Math.PI);
          ctx.fillStyle = node.color ? `${node.color}33` : 'rgba(99,102,241,0.2)';
          ctx.fill();
        }

        // Core circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = node.color || '#6366F1';
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#0B0F19';
        ctx.stroke();

        // Node label
        ctx.font = `${node.type === 'me' ? 'bold 12px' : '11px'} Plus Jakarta Sans`;
        ctx.fillStyle = '#E2E8F0';
        ctx.textAlign = 'center';
        ctx.fillText(node.label, node.x, node.y + radius + 13);
      }

      animId = requestAnimationFrame(tick);
    };

    animId = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animId);
    };
  }, [nodes, links, selectedNode]);

  // Handle click on canvas node
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const clickX = ((e.clientX - rect.left) / rect.width) * canvas.width;
    const clickY = ((e.clientY - rect.top) / rect.height) * canvas.height;

    let clicked: GraphNode | null = null;
    for (const node of nodes) {
      if (node.x && node.y) {
        const dist = Math.hypot(node.x - clickX, node.y - clickY);
        if (dist <= (node.size || 14) + 6) {
          clicked = node;
          break;
        }
      }
    }
    setSelectedNode(clicked);
  };

  return (
    <div className="relative w-full h-[520px] bg-[#111726]/80 rounded-2xl border border-slate-800/80 backdrop-blur-md overflow-hidden flex flex-col shadow-xl">
      {/* Header bar */}
      <div className="px-4 py-3 border-b border-slate-800/80 bg-slate-900/60 flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <Users className="w-4 h-4 text-indigo-400" />
          <h2 className="text-sm font-semibold text-slate-200">Event Relationship Graph</h2>
          <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700/60 font-mono">
            {nodes.length} nodes
          </span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer"
          title="Refresh Graph"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Legend */}
      <div className="px-4 py-1.5 bg-slate-900/40 border-b border-slate-800/50 flex items-center gap-4 text-[11px] text-slate-400 overflow-x-auto">
        <span className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[#6366F1]" /> People
        </span>
        <span className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" /> Topics
        </span>
        <span className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[#06B6D4]" /> Companies
        </span>
        <span className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" /> Ideas
        </span>
        <span className="flex items-center gap-1.5 whitespace-nowrap">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EC4899]" /> Recs
        </span>
      </div>

      {/* Canvas */}
      <div className="relative flex-1 cursor-pointer">
        <canvas
          ref={canvasRef}
          width={700}
          height={420}
          onClick={handleCanvasClick}
          className="w-full h-full"
        />

        {nodes.length === 0 && (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
            <Users className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">No connections captured yet</p>
            <p className="text-xs text-slate-600 mt-1">Talk to Wingman to log contacts and topics.</p>
          </div>
        )}
      </div>

      {/* Selected Node Details Drawer */}
      {selectedNode && (
        <div className="absolute bottom-3 left-3 right-3 bg-slate-900/95 border border-indigo-500/40 rounded-xl p-3.5 shadow-2xl backdrop-blur-md z-20 animate-in fade-in duration-200">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: selectedNode.color }}
                />
                <h4 className="font-semibold text-slate-100 text-sm">{selectedNode.label}</h4>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {selectedNode.type}
                </span>
              </div>
              {selectedNode.company && (
                <p className="text-xs text-slate-400 mt-0.5 font-medium">
                  {selectedNode.company} {selectedNode.role ? `• ${selectedNode.role}` : ''}
                </p>
              )}
            </div>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {selectedNode.topics && selectedNode.topics.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {selectedNode.topics.map((t, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 text-[11px] rounded-full bg-emerald-950/60 text-emerald-300 border border-emerald-800/40"
                >
                  {t}
                </span>
              ))}
            </div>
          )}

          {selectedNode.fullText && (
            <p className="text-xs text-slate-300 mt-2 bg-slate-800/60 p-2 rounded border border-slate-700/50 italic">
              "{selectedNode.fullText}"
            </p>
          )}
        </div>
      )}
    </div>
  );
};

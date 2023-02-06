import React, { useCallback, useEffect } from 'react';
import { ForceGraph3D } from 'react-force-graph';
import Table from './components/Table';
import { Graph } from './types';
import * as THREE from 'three';
import data_raw from './data.json';


const data = data_raw as Graph;
const obj: Graph = {
    nodes: [
        { id: '3', label: "Truong", rank: 2, popularity: 200, size: 12, color: 'cyan' },
        { id: '2', label: "Nhat", rank: 1, popularity: 100, size: 18, color: 'pink' },
        { id: '4', label: "Nhat", rank: 3, popularity: 100, size: 6, color: 'cyan' },

    ], links: [
        { source: '2', target: '3', weight: 10 },
        { source: '4', target: '3', weight: 2 },
        { source: '4', target: '2', weight: 2 },
    ]
};
// const geometry = new THREE.SphereGeometry(15, 32, 16);
// const material = new THREE.MeshBasicMaterial({ color: 0xffff00 });
// const material1 = new THREE.MeshLambertMaterial({
//     color: Math.round(Math.random() * Math.pow(2, 24)),
//     transparent: true,
//     opacity: 0.75
// })
// const sphere = new THREE.Mesh(geometry, material);
// const sphere1 = new THREE.Mesh(geometry, material1);


function App() {
    const [focusingNode, setFocusingNode] = React.useState<string | null>(null);
    const fgRef = React.useRef(undefined);
    const handleNodeFocus = (id: string) => {
        // find node
        //@ts-ignore
        const hehe = fgRef.current.getGraphBbox((node) => node.id === id);
        const sum = (a: number, b: number) => a + b
        const node = {
            x: hehe.x.reduce(sum) / hehe.x.length,
            y: hehe.y.reduce(sum) / hehe.y.length,
            z: hehe.z.reduce(sum) / hehe.z.length,
        }
        console.log(node)

        // Aim at node from outside it
        const distance = 60;
        const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);


        //@ts-ignore
        fgRef.current.cameraPosition(
            { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
            node, // lookAt ({ x, y, z })
            2000  // ms transition duration
        );
        // //@ts-ignore
        // fgRef.current.zoomToFit(1000, 50, (node) => node.id === id)
    };
    useEffect(() => {
        if (focusingNode) {
            handleNodeFocus(focusingNode)
        }
    }, [focusingNode, fgRef]);

    return (
        <div className="select-none"
            onClick={() => { setFocusingNode(null) }}
        >
            <ForceGraph3D
                ref={fgRef}
                graphData={data}
                nodeVal={'size'}
                nodeLabel={'label'}
                nodeColor={'color'}
                onNodeClick={(node) => typeof node.id == 'string' && setFocusingNode(node.id)}
            // linkDirectionalParticles={'weight'}
            // linkDirectionalParticleSpeed={0}
            // warmupTicks={100}
            // cooldownTicks={0}
            // nodeThreeObject={(node) => {
            //     if (node. === focusingNode) {
            //         return sphere
            //     } else return sphere1
            // }}

            />
            <Table graph={data} setFocusingNode={setFocusingNode} focusingNode={focusingNode} />
        </div>
    );
}

export default App;

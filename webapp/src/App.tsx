import React from 'react';
import { ForceGraph3D } from 'react-force-graph';
import Table from './components/Table';
import { Graph } from './types';
import * as THREE from 'three';


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
const geometry = new THREE.SphereGeometry(15, 32, 16);
const material = new THREE.MeshBasicMaterial({ color: 0xffff00 });
const material1 = new THREE.MeshLambertMaterial({
    color: Math.round(Math.random() * Math.pow(2, 24)),
    transparent: true,
    opacity: 0.75
})
const sphere = new THREE.Mesh(geometry, material);
const sphere1 = new THREE.Mesh(geometry, material1);


function App() {
    const [focusingNode, setFocusingNode] = React.useState<string | null>(null);
    return (
        <div className="select-none"
            onClick={() => { setFocusingNode(null) }}
        >
            <ForceGraph3D
                graphData={obj}
                nodeVal={'size'}
                nodeLabel={'label'}
                nodeColor={'color'}
                linkDirectionalParticles={'weight'}
                linkDirectionalParticleSpeed={0}
            // nodeThreeObject={(node) => {
            //     if (node.id === focusingNode) {
            //         return sphere
            //     } else return sphere1
            // }}

            />
            <Table graph={obj} setFocusingNode={setFocusingNode} focusingNode={focusingNode} />
        </div>
    );
}

export default App;

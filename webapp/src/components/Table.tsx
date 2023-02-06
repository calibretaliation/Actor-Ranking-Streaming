import React from 'react';
import Row from './Row';
import { Graph } from '../types';

type Props = {
    graph: Graph;
    focusingNode: string | null;
    setFocusingNode: React.Dispatch<React.SetStateAction<string | null>>;
};

const Table: React.FC<Props> = ({ graph, setFocusingNode, focusingNode }) => {
    return (
        // <div className={"h-full absolute top-0 right-0 p-10 flex flex-1"}>
        <div className='absolute top-10 right-10 bottom-10 flex flex-col w-64 bg-[rgba(155,155,155,0.1)] rounded-lg text-white py-2 px-2 items-center'>
            <div className='flex flex-row gap-2 items-center mt-2'>
                <div className='rounded-full h-3 w-3 bg-[rgb(187,47,47)] border-white border'></div>
                <h1 className='text-xl bold'>Live Rank Celebs</h1>
            </div>
            <h2 className='mb-5 text-xs italic'>Last updated at {new Date().getHours()}:{('0' + new Date().getMinutes()).substr(-2)}</h2>
            <div className='flex flex-row justify-between text-sm px-3 py-1 w-full'>
                <div className='flex flex-row'>
                    <p className='w-12'>#</p>
                    <p>Name</p>
                </div>
                <p>Popularity</p>
            </div>
            <div className='h-px w-11/12 bg-white mb-2 mt-0.5'></div>
            <div className='overflow-y-auto w-full flex-1 scrollbar'>
                {graph.nodes.sort((a, b) => a.rank > b.rank ? 1 : -1).slice(0, 100).map(
                    (row) => <Row node={row} key={row.id} focusingNode={focusingNode} setFocusingNode={setFocusingNode} />
                )}
            </div>
            <h2 className='text-xs italic mt-2'>From UpdateEverday with ♥</h2>
        </div>
        // </div>
    );
};

export default Table;
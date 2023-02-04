import React from 'react';
import Row from './Row';
import { Graph } from '../types';
import { keyboard } from '@testing-library/user-event/dist/keyboard';

type Props = {
    graph: Graph;
    focusingNode: string | null;
    setFocusingNode: React.Dispatch<React.SetStateAction<string | null>>;
};

const Table: React.FC<Props> = ({ graph, setFocusingNode, focusingNode }) => {
    return (
        <div className={"h-full absolute top-0 right-0 p-10 flex flex-1"}>
            <div className='flex flex-col h-full w-64 bg-[rgba(155,155,155,0.1)] rounded-lg text-white p-4 items-center'>
                <div className='flex flex-row gap-2 items-center'>
                    <div className='rounded-full h-3 w-3 bg-[rgb(187,47,47)] border-white border'></div>
                    <h1 className='text-xl bold'>Live Rank Celebs</h1>
                </div>
                <h2 className='mb-5 text-xs italic'>Last updated at 23:45</h2>
                <div className='flex flex-row justify-between text-sm p-1 w-full'>
                    <div className='flex flex-row'>
                        <p className='w-12'>#</p>
                        <p>Name</p>
                    </div>
                    <p>Popularity</p>
                </div>
                <div className='h-px w-full bg-white mb-2 mt-1'></div>
                <div className='overflow-y w-full flex-1'>
                    {graph.nodes.sort((a, b) => a.rank > b.rank ? 1 : -1).map(
                        (row) => <Row node={row} key={row.id} focusingNode={focusingNode} setFocusingNode={setFocusingNode} />
                    )}
                </div>
                <h2 className='text-xs italic'>From UpdateEverday with ♥</h2>
            </div>
        </div>
    );
};

export default Table;
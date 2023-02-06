import React from 'react';
import { NodeType } from '../types';

type Props = {
    node: NodeType;
    focusingNode: string | null;
    setFocusingNode: React.Dispatch<React.SetStateAction<string | null>>;
};

const Row: React.FC<Props> = ({ node, focusingNode, setFocusingNode }) => {
    return (
        <div className={`flex flex-row justify-between hover:bg-[rgba(155,155,155,0.1)] cursor-pointer py-1.5 px-3 text-sm rounded w-full ${focusingNode === node.id && "bg-[rgba(155,155,155,0.3)] hover:bg-[rgba(155,155,155,0.3)]"}`}
            onClick={(e) => { setFocusingNode(node.id); e.stopPropagation(); }}
        >
            <div className='flex flex-row'>
                <p className='w-12'>{node.rank}</p>
                <p>{node.label}</p>
            </div>
            <p>{node.popularity}</p>
        </div >
    );
};
export default Row;
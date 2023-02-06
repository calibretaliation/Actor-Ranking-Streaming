export type Graph = {
    nodes: NodeType[],
    links: Link[],
}
export type NodeType = {
    id: string,
    label: string,
    rank: number,
    popularity: number,
    size: number,
    color: string,
}
export type Link = {
    source: string,
    target: string,
    weight: number,
}
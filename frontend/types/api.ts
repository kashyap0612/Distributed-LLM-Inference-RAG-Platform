export type Chunk = { text:string; score:number; source:string; chunk_id:string };
export type RouteDecision = { model:string; confidence:number; complexity:number; reasons:string[] };
export type Trace = { stage:string; status:string; detail?:Record<string, unknown> };

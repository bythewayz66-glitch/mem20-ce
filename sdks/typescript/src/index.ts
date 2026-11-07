/**
 * mem20-ce TypeScript SDK skeleton
 * Apache-2.0
 */

export interface ContaminationReport {
  contamination_rate: number;
  grounded_count: number;
  simulated_count: number;
  violations: string[];
  healthy: boolean;
}

export interface RecallHit {
  score: number;
  record: Record<string, unknown>;
}

export class Mem20CEClient {
  constructor(private storePath: string = "~/.mem20-ce/store") {}

  async remember(_content: string, _tags: string[] = []): Promise<string> {
    throw new Error("Wire to mem20-ce CLI or HTTP in next increment");
  }

  async recall(_query: string, _k = 5): Promise<{ hits: RecallHit[]; healthy: boolean }> {
    throw new Error("Wire to mem20-ce CLI or HTTP in next increment");
  }

  async contamination(): Promise<ContaminationReport> {
    throw new Error("Wire to mem20-ce CLI or HTTP in next increment");
  }
}

export const VERSION = "0.1.0";

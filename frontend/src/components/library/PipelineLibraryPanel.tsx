import { Play, Trash2, FolderOpen } from "lucide-react";
import type { Pipeline } from "../../types";

type Props = {
  pipelines: Pipeline[];
  onRun: (pipeline: Pipeline) => Promise<void>;
  onLoad: (pipeline: Pipeline) => void;
  onDelete: (id: string) => Promise<void>;
};

export function PipelineLibraryPanel({ pipelines, onRun, onLoad, onDelete }: Props) {
  return (
    <section className="panel-card">
      <div className="panel-header">
        <div>
          <h2>Pipeline Library</h2>
          <p>Load, run, or remove saved workflow definitions.</p>
        </div>
      </div>
      <div className="panel-list">
        {pipelines.map((pipeline) => (
          <article className="library-card" key={pipeline.id}>
            <div>
              <h3>{pipeline.name}</h3>
              <p>{pipeline.description}</p>
            </div>
            <div className="row-actions">
              <button type="button" className="secondary-button" onClick={() => onLoad(pipeline)}>
                <FolderOpen size={14} />
                Open
              </button>
              <button type="button" className="secondary-button" onClick={() => onRun(pipeline)}>
                <Play size={14} />
                Run
              </button>
              <button type="button" className="icon-button danger" onClick={() => onDelete(pipeline.id)}>
                <Trash2 size={14} />
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

import { Plus } from "lucide-react";
import type { ExecutorCatalogItem } from "../../types";

type Props = {
  items: ExecutorCatalogItem[];
  onCreateNode: (type: ExecutorCatalogItem["type"]) => void;
};

export function NodePalette({ items, onCreateNode }: Props) {
  return (
    <div className="panel-list">
      {items.map((item) => (
        <button
          key={item.type}
          className="catalog-card"
          draggable
          onDragStart={(event) => event.dataTransfer.setData("application/workflow-executor", item.type)}
          onClick={() => onCreateNode(item.type)}
        >
          <div className="catalog-card-top">
            <div>
              <div className="catalog-title">{item.label}</div>
              <div className="catalog-category">{item.category}</div>
            </div>
            <Plus size={14} />
          </div>
          <p>{item.description}</p>
        </button>
      ))}
    </div>
  );
}

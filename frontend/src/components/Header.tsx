import { Activity, GitBranch, Database, Workflow, Save, PlayCircle, Plus } from "lucide-react";

type HeaderProps = {
  activeTab: "canvas" | "connections" | "pipelines" | "monitoring";
  onTabChange: (tab: HeaderProps["activeTab"]) => void;
  onSave: () => void | Promise<void>;
  onRun: () => void | Promise<void>;
  onNewWorkflow: () => void;
};

export function Header({ activeTab, onTabChange, onSave, onRun, onNewWorkflow }: HeaderProps) {
  return (
    <header className="header">
      <div className="brand-block">
        <div className="brand-mark">WF</div>
        <div>
          <div className="brand-title">Workflow Studio</div>
          <div className="brand-subtitle">Visual ETL builder for agent-driven pipelines</div>
        </div>
      </div>

      <nav className="header-nav">
        {[
          { key: "canvas", label: "Canvas", icon: Workflow },
          { key: "connections", label: "Connections", icon: Database },
          { key: "pipelines", label: "Pipelines", icon: GitBranch },
          { key: "monitoring", label: "Monitoring", icon: Activity },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.key}
              type="button"
              className={`nav-pill ${activeTab === item.key ? "active" : ""}`}
              onClick={() => onTabChange(item.key as HeaderProps["activeTab"])}
            >
              <Icon size={15} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="header-actions">
        <button type="button" className="secondary-button" onClick={onNewWorkflow}>
          <Plus size={16} />
          New
        </button>
        <button type="button" className="secondary-button" onClick={onSave}>
          <Save size={16} />
          Save
        </button>
        {/* <button type="button" className="primary-button" onClick={onRun}>
          <PlayCircle size={16} />
          Run
        </button> */}
      </div>
    </header>
  );
}

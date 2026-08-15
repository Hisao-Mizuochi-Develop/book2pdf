import { Camera, Crop, FileUp, Package } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { type AppView, useNavigationStore } from "@/store/navigationStore";

interface NavItem {
  view: AppView;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { view: "capture", label: "キャプチャ", icon: Camera },
  { view: "trim", label: "トリミング", icon: Crop },
  { view: "pdf", label: "PDF読込", icon: FileUp },
  { view: "export", label: "ZIP出力", icon: Package },
];

export function Sidebar() {
  const { currentView, setView } = useNavigationStore();

  return (
    <aside className="w-[200px] flex flex-col border-r bg-background">
      <div className="flex h-14 items-center px-5">
        <span className="text-sm font-semibold tracking-tight">book2pdf</span>
      </div>
      <nav className="flex flex-1 flex-col gap-1 px-3 py-4">
        {navItems.map(({ view, label, icon: Icon }) => {
          const active = currentView === view;
          return (
            <Button
              key={view}
              variant="ghost"
              onClick={() => setView(view)}
              className={cn(
                "h-10 justify-start gap-3 rounded-lg px-3 text-sm font-normal transition-colors",
                active
                  ? "bg-[#F5F5F7] text-foreground font-medium relative before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:h-5 before:w-[3px] before:rounded-r-full before:bg-foreground"
                  : "text-muted-foreground hover:bg-[#F5F5F7] hover:text-foreground"
              )}
            >
              <Icon className="size-4" />
              {label}
            </Button>
          );
        })}
      </nav>
    </aside>
  );
}

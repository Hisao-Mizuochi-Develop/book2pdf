import { MainLayout } from "@/components/layout/MainLayout";
import { useNavigationStore } from "@/store/navigationStore";
import { CaptureView } from "@/views/CaptureView";
import { TrimView } from "@/views/TrimView";
import { PdfImportView } from "@/views/PdfImportView";
import { ExportView } from "@/views/ExportView";

const viewMap = {
  capture: CaptureView,
  trim: TrimView,
  pdf: PdfImportView,
  export: ExportView,
};

function App() {
  const currentView = useNavigationStore((state) => state.currentView);
  const View = viewMap[currentView];

  return (
    <MainLayout>
      <View />
    </MainLayout>
  );
}

export default App;

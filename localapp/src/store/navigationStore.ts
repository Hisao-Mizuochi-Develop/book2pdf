import { create } from "zustand";

export type AppView = "capture" | "trim" | "pdf" | "export";

export interface NavigationState {
  currentView: AppView;
  setView: (view: AppView) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  currentView: "capture",
  setView: (view) => set({ currentView: view }),
}));

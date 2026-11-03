import {
  createContext,
  useContext,
  useEffect,
  useReducer,
  useState,
} from "react";
import type { Dispatch, ReactNode } from "react";
import { reducer, restoreState, STORE_KEY } from "../domain/model";
import type { Action, State } from "../domain/model";
const Context = createContext<{
  state: State;
  dispatch: Dispatch<Action>;
  storageAvailable: boolean;
} | null>(null);
export function StoreProvider({ children }: { children: ReactNode }) {
  const [storageAvailable, setStorageAvailable] = useState(true);
  const [state, dispatch] = useReducer(reducer, undefined, () => {
    try {
      return restoreState(localStorage.getItem(STORE_KEY));
    } catch {
      return restoreState(null);
    }
  });
  useEffect(() => {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({ version: 1, state }));
    } catch {
      setStorageAvailable(false);
    }
  }, [state]);
  useEffect(() => {
    if (
      state.incident !== "active" ||
      state.estimateUpdated ||
      state.globalPaused ||
      state.dataStatus !== "ready" ||
      !state.services.some((s) => s.id === "checkout-service" && !s.paused)
    )
      return;
    const t = setTimeout(() => dispatch({ type: "estimate-update" }), 30000);
    return () => clearTimeout(t);
  }, [
    state.incident,
    state.estimateUpdated,
    state.globalPaused,
    state.dataStatus,
    state.services,
  ]);
  return (
    <Context.Provider value={{ state, dispatch, storageAvailable }}>
      {children}
    </Context.Provider>
  );
}
export function useStore() {
  const value = useContext(Context);
  if (!value) throw new Error("StoreProvider ausente");
  return value;
}

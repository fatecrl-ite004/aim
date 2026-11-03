import { useEffect, useState } from "react";
import { useStore } from "./state/Store";
import { Banner, Button, EmptyState, Toggle } from "./components/ui";
import type { Notify } from "./components/ui";
import { Demo } from "./components/Demo";
import { Dashboard } from "./pages/Dashboard";
import { ServiceDetail } from "./pages/ServiceDetail";
import { Services } from "./pages/Services";
import { Notifications } from "./pages/Notifications";
import { Audit } from "./pages/Audit";
function useRoute() {
  const read = () => window.location.hash.slice(1) || "/";
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const f = () => setRoute(read());
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  return route;
}
export function App() {
  const { state, dispatch, storageAvailable } = useStore(),
    route = useRoute(),
    [demo, setDemo] = useState(false),
    [toast, setToast] = useState<{
      message: string;
      tone: "success" | "critical";
    } | null>(null),
    page = route.split("?")[0],
    active = page.startsWith("/servico/") ? "/" : page;
  const notify: Notify = (message, tone = "success") =>
    setToast({ message, tone });
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 6000);
    return () => clearTimeout(t);
  }, [toast]);
  useEffect(() => {
    document.querySelector(".workspace-scroll")?.scrollTo(0, 0);
  }, [route]);
  let serviceId = "";
  try {
    serviceId = decodeURIComponent(page.slice("/servico/".length));
  } catch {
    serviceId = "";
  }
  const nav = [
    ["/", "Visão geral"],
    ["/auditoria", "Auditoria e testes"],
    ["/servicos", "Serviços"],
    ["/notificacoes", "Notificações"],
  ];
  return (
    <div className="app-shell">
      <a
        href="#main-content"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          document.getElementById("main-content")?.focus();
        }}
      >
        Pular para o conteúdo
      </a>
      <aside className="sidebar">
        <a className="brand" href="#/" aria-label="AIM, visão geral">
          AIM
        </a>
        <p className="brand-caption">EMENDATA / OBSERVABILIDADE</p>
        <nav aria-label="Navegação principal">
          {nav.map(([path, label]) => (
            <a
              href={"#" + path}
              key={path}
              aria-current={active === path ? "page" : undefined}
            >
              {label}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <p>
            Emendata
            <br />
            Ambiente de demonstração
          </p>
          <Button onClick={() => setDemo(true)}>Demonstração</Button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span>Produção / malha principal</span>
          <Toggle
            global
            checked={!state.globalPaused}
            label={
              state.globalPaused ? "Sentinela em pausa" : "Sentinela ativo"
            }
            ariaLabel="Sentinela global"
            onChange={() => dispatch({ type: "global-toggle" })}
          />
        </header>
        <main id="main-content" tabIndex={-1} className="workspace-scroll">
          {!storageAvailable && (
            <Banner tone="attention" title="Persistência local indisponível">
              Os dados desta sessão funcionarão, mas poderão ser perdidos ao
              recarregar a página.
            </Banner>
          )}
          {state.globalPaused && (
            <Banner title="Ⅱ Sentinela global em pausa">
              A conectividade é mantida. O risco não está sendo avaliado; as
              pausas individuais serão preservadas ao retomar.
            </Banner>
          )}
          {page === "/" ? (
            <Dashboard />
          ) : page === "/servicos" ? (
            <Services
              key={route}
              notify={notify}
              openNew={
                new URLSearchParams(route.split("?")[1]).get("novo") === "1"
              }
            />
          ) : page === "/notificacoes" ? (
            <Notifications notify={notify} />
          ) : page === "/auditoria" ? (
            <Audit notify={notify} />
          ) : page.startsWith("/servico/") ? (
            <ServiceDetail id={serviceId} notify={notify} />
          ) : (
            <EmptyState
              title="Página não encontrada"
              action={
                <a className="button primary" href="#/">
                  Voltar à visão geral
                </a>
              }
            >
              Escolha uma opção no menu lateral para continuar.
            </EmptyState>
          )}
        </main>
      </div>
      {demo && <Demo onClose={() => setDemo(false)} notify={notify} />}{" "}
      {toast && (
        <div
          className={`toast ${toast.tone}`}
          role={toast.tone === "critical" ? "alert" : "status"}
        >
          <span>
            {toast.tone === "success" ? "✓" : "!"} {toast.message}
          </span>
          <button
            aria-label="Dispensar mensagem"
            onClick={() => setToast(null)}
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}

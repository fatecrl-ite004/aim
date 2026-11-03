import { useEffect, useId, useRef } from "react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
export function Button({
  tone = "secondary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  tone?: "primary" | "secondary" | "danger" | "quiet";
}) {
  return (
    <button
      type="button"
      className={`button ${tone} ${className}`}
      {...props}
    />
  );
}
export function Banner({
  tone = "info",
  title,
  children,
}: {
  tone?: "info" | "success" | "attention" | "critical";
  title: string;
  children?: ReactNode;
}) {
  return (
    <div
      className={`banner ${tone}`}
      role={tone === "critical" ? "alert" : undefined}
    >
      <strong>{title}</strong>
      {children && <div>{children}</div>}
    </div>
  );
}
export function Toggle({
  checked,
  onChange,
  label,
  disabled = false,
  global = false,
  ariaLabel,
}: {
  checked: boolean;
  onChange: () => void;
  label: string;
  disabled?: boolean;
  global?: boolean;
  ariaLabel?: string;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={ariaLabel || label}
      disabled={disabled}
      className={`toggle ${checked ? "on" : "off"} ${global ? "global-toggle" : ""}`}
      onClick={(e) => {
        e.stopPropagation();
        onChange();
      }}
    >
      {checked ? (
        <img
          src={`${import.meta.env.BASE_URL}assets/${global ? "fd6e3" : "9a3e8"}.svg`}
          width="36"
          height="20"
          alt=""
        />
      ) : (
        <span className="off-track" aria-hidden="true">
          <span />
        </span>
      )}
      <span>{label}</span>
    </button>
  );
}
export function Dialog({
  title,
  children,
  onClose,
  wide = false,
  drawer = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
  drawer?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null),
    id = useId(),
    closeRef = useRef(onClose);
  closeRef.current = onClose;
  useEffect(() => {
    const d = ref.current!;
    if (!d.open) d.showModal();
    return () => {
      if (d.open) d.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`dialog ${wide ? "wide" : ""} ${drawer ? "drawer" : ""}`}
      aria-labelledby={id}
      onCancel={(e) => {
        e.preventDefault();
        closeRef.current();
      }}
    >
      <div className="dialog-heading">
        <h2 id={id}>{title}</h2>
        <Button
          tone="quiet"
          className="close-button"
          aria-label={`Fechar ${title}`}
          onClick={onClose}
        >
          ×
        </Button>
      </div>
      {children}
    </dialog>
  );
}
export function EmptyState({
  title,
  children,
  action,
}: {
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="empty-state">
      <span className="empty-mark" aria-hidden="true">
        ○
      </span>
      <h2>{title}</h2>
      <p>{children}</p>
      {action}
    </section>
  );
}
export function SettingsTabs({
  active,
}: {
  active: "services" | "notifications";
}) {
  return (
    <nav className="settings-tabs" aria-label="Configurações">
      <a
        href="#/servicos"
        className={`button ${active === "services" ? "primary" : "secondary"}`}
        aria-current={active === "services" ? "page" : undefined}
      >
        Serviços
      </a>
      <a
        href="#/notificacoes"
        className={`button ${active === "notifications" ? "primary" : "secondary"}`}
        aria-current={active === "notifications" ? "page" : undefined}
      >
        Notificações
      </a>
    </nav>
  );
}
export function PageHeading({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <header className="page-heading">
      <h1>{title}</h1>
      <p>{children}</p>
    </header>
  );
}
export type Notify = (message: string, tone?: "success" | "critical") => void;

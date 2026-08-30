"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Loading } from "@/components/ui/Loading";
import { useAuth } from "@/features/auth/AuthProvider";
import { ConversationSidebar } from "@/features/conversations/components/ConversationSidebar";
import {
  ConversationProvider,
  useConversationContext,
} from "@/features/conversations/ConversationProvider";
import { HealthPills } from "@/features/health/components/HealthPills";
import { useHealth } from "@/features/health/hooks";
import { cn } from "@/lib/utils";

type DashboardSidebarContentProps = {
  onNavigate?: () => void;
};

// ────────────────────────────────────────────────────────
// DashboardSidebarContent
// Feature: dashboard shell
// Use: shared sidebar body for desktop panel and mobile drawer.
// ────────────────────────────────────────────────────────

function DashboardSidebarContent({ onNavigate }: DashboardSidebarContentProps) {
  const pathname = usePathname();
  const { logout, userEmail } = useAuth();
  const { health } = useHealth();
  const { conversations, activeId, refresh, selectConversation, startNewConversation } =
    useConversationContext();

  const isChat = pathname === "/chat";

  return (
    <>
      <div className="border-b border-line px-4 pb-3 pt-[18px]">
        <h1 className="text-base font-semibold tracking-wide">AI Chat</h1>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          LangChain = AI components
          <br />
          RAG = Knowledge + LLM
        </p>
        <HealthPills health={health} />
        {userEmail ? (
          <small className="mt-2 block truncate text-[11px] text-muted">{userEmail}</small>
        ) : null}
      </div>

      <nav className="flex gap-2 border-b border-line p-3">
        <Link
          href="/chat"
          onClick={onNavigate}
          className={cn(
            "flex-1 rounded-[10px] border px-2.5 py-2 text-center text-[13px] no-underline",
            isChat
              ? "border-line bg-panel-2 text-text"
              : "border-transparent text-muted hover:bg-panel-2 hover:text-text",
          )}
        >
          Chat
        </Link>
        <Link
          href="/knowledge"
          onClick={onNavigate}
          className={cn(
            "flex-1 rounded-[10px] border px-2.5 py-2 text-center text-[13px] no-underline",
            pathname === "/knowledge"
              ? "border-line bg-panel-2 text-text"
              : "border-transparent text-muted hover:bg-panel-2 hover:text-text",
          )}
        >
          Knowledge
        </Link>
      </nav>

      {isChat ? (
        <>
          <div className="flex flex-wrap gap-2 p-3">
            <Button
              type="button"
              onClick={() => {
                startNewConversation();
                onNavigate?.();
              }}
            >
              New chat
            </Button>
            <Button type="button" variant="ghost" onClick={() => void refresh()}>
              Refresh
            </Button>
          </div>
          <ConversationSidebar
            conversations={conversations}
            activeId={activeId}
            onSelect={(id) => {
              void selectConversation(id);
              onNavigate?.();
            }}
          />
        </>
      ) : null}

      <div className="mt-auto border-t border-line p-3">
        <Button
          type="button"
          variant="ghost"
          className="w-full"
          onClick={() => void logout()}
        >
          Log out
        </Button>
      </div>
    </>
  );
}

// ────────────────────────────────────────────────────────
// MobileBottomNav
// Feature: dashboard shell
// Use: fixed bottom tabs for primary routes on small screens.
// ────────────────────────────────────────────────────────

function MobileBottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-2 border-t border-line bg-panel/95 pb-[env(safe-area-inset-bottom)] md:hidden"
      aria-label="Main navigation"
    >
      <Link
        href="/chat"
        className={cn(
          "px-4 py-3 text-center text-[13px] font-medium no-underline",
          pathname === "/chat" ? "text-accent" : "text-muted",
        )}
      >
        Chat
      </Link>
      <Link
        href="/knowledge"
        className={cn(
          "px-4 py-3 text-center text-[13px] font-medium no-underline",
          pathname === "/knowledge" ? "text-accent" : "text-muted",
        )}
      >
        Knowledge
      </Link>
    </nav>
  );
}

// ────────────────────────────────────────────────────────
// DashboardShell
// Feature: dashboard shell
// Use: authenticated layout with sidebar and main content area.
// ────────────────────────────────────────────────────────

function DashboardShell({ children }: { children: ReactNode }) {
  const { authReady, isAuthenticated } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const { activeTitle } = useConversationContext();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (authReady && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authReady, isAuthenticated, router]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!mobileOpen) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setMobileOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [mobileOpen]);

  if (!authReady) return <Loading />;
  if (!isAuthenticated) return <Loading label="Redirecting…" />;

  const mobileTitle =
    pathname === "/knowledge" ? "Knowledge" : activeTitle || "Chat";

  return (
    <div className="grid h-dvh min-h-0 grid-cols-1 md:h-full md:grid-cols-[280px_1fr]">
      <aside className="hidden min-h-0 min-w-0 flex-col border-r border-line bg-panel/95 md:flex">
        <DashboardSidebarContent />
      </aside>

      {mobileOpen ? (
        <div className="fixed inset-0 z-40 md:hidden" role="presentation">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-black/55"
            onClick={() => setMobileOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-[min(100vw-3rem,280px)] flex-col border-r border-line bg-panel shadow-xl">
            <DashboardSidebarContent onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      ) : null}

      <div className="flex min-h-0 min-w-0 flex-1 flex-col pb-[calc(3rem+env(safe-area-inset-bottom))] md:pb-0">
        <header className="flex shrink-0 items-center gap-3 border-b border-line bg-panel/95 px-4 py-3 md:hidden">
          <button
            type="button"
            aria-label="Open menu"
            aria-expanded={mobileOpen}
            className="rounded-[10px] border border-line px-2.5 py-2 text-sm text-text"
            onClick={() => setMobileOpen(true)}
          >
            Menu
          </button>
          <span className="min-w-0 flex-1 truncate text-sm font-semibold">{mobileTitle}</span>
        </header>
        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      </div>

      <MobileBottomNav />
    </div>
  );
}

// ────────────────────────────────────────────────────────
// DashboardLayout
// Feature: dashboard shell
// Use: wrap dashboard routes with auth, conversations, and sidebar.
// ────────────────────────────────────────────────────────

export function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <ConversationProvider>
      <DashboardShell>{children}</DashboardShell>
    </ConversationProvider>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

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

// ────────────────────────────────────────────────────────
// DashboardSidebar
// Feature: dashboard shell
// Use: left sidebar with nav, health pills, and chat thread list.
// ────────────────────────────────────────────────────────

function DashboardSidebar() {
  const pathname = usePathname();
  const { logout, userEmail } = useAuth();
  const { health } = useHealth();
  const { conversations, activeId, refresh, selectConversation, startNewConversation } =
    useConversationContext();

  const isChat = pathname === "/chat";

  return (
    <aside className="hidden min-w-0 flex-col border-r border-line bg-panel/95 md:flex">
      <div className="border-b border-line px-4 pb-3 pt-[18px]">
        <h1 className="text-base font-semibold tracking-wide">AI Chat</h1>
        <p className="mt-2 text-xs leading-relaxed text-muted">
          LangChain = AI components
          <br />
          RAG = Knowledge + LLM
        </p>
        <HealthPills health={health} />
        {userEmail ? (
          <small className="mt-2 block text-[11px] text-muted">{userEmail}</small>
        ) : null}
      </div>

      <nav className="flex gap-2 border-b border-line p-3">
        <Link
          href="/chat"
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
          <div className="flex gap-2 p-3">
            <Button type="button" onClick={() => startNewConversation()}>
              New chat
            </Button>
            <Button type="button" variant="ghost" onClick={() => void refresh()}>
              Refresh
            </Button>
          </div>
          <ConversationSidebar
            conversations={conversations}
            activeId={activeId}
            onSelect={(id) => void selectConversation(id)}
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
    </aside>
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

  useEffect(() => {
    if (authReady && !isAuthenticated) {
      router.replace("/login");
    }
  }, [authReady, isAuthenticated, router]);

  if (!authReady) return <Loading />;
  if (!isAuthenticated) return <Loading label="Redirecting…" />;

  return (
    <div className="grid h-full grid-cols-1 md:grid-cols-[280px_1fr]">
      <DashboardSidebar />
      <div className="flex min-w-0 flex-1 flex-col">{children}</div>
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

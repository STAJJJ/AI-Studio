"use client";

import { FormEvent } from "react";
import { Bot, Eraser, MessageSquare, Plus, Send, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useChat } from "@/hooks/use-chat";

export function ChatPanel() {
  const {
    roles,
    selectedRoleId,
    model,
    messages,
    input,
    rolesLoading,
    sending,
    streaming,
    error,
    rolesError,
    canSend,
    setInput,
    selectRole,
    sendMessage,
    stopGeneration,
    clearConversation,
    newConversation,
    loadRoles,
  } = useChat();
  const selectedRole = roles.find((role) => role.id === selectedRoleId);
  const roleDescription = rolesLoading
    ? "Loading roles from FastAPI..."
    : rolesError
      ? "Unable to load roles from FastAPI."
      : selectedRole?.description ?? "No role selected.";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await sendMessage();
  }

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-6 py-8">
      <header className="space-y-1">
        <div className="space-y-1">
          <p className="text-sm font-medium uppercase tracking-wide text-primary">AI Chat</p>
          <h1 className="text-3xl font-semibold tracking-normal">Chat with AI Studio</h1>
          <p className="text-sm text-muted-foreground">Streaming chat through FastAPI and the LLM Gateway.</p>
        </div>
      </header>

      <section className="grid flex-1 gap-6 lg:grid-cols-[360px_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Session</CardTitle>
            <CardDescription>Browser-only conversation memory for the current demo.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <select
                id="role"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                disabled={sending || rolesLoading || roles.length === 0}
                value={selectedRoleId}
                onChange={(event) => selectRole(event.target.value)}
              >
                {roles.map((role) => (
                  <option key={role.id} value={role.id}>
                    {role.name}
                  </option>
                ))}
              </select>
              <p className="text-sm leading-6 text-muted-foreground">{roleDescription}</p>
              {rolesError ? (
                <div className="space-y-3 rounded-md border border-destructive/30 bg-destructive/10 p-3">
                  <p className="text-sm text-destructive">{rolesError}</p>
                  <Button type="button" variant="outline" size="sm" onClick={loadRoles}>
                    Retry
                  </Button>
                </div>
              ) : null}
            </div>

            <div className="rounded-md border bg-muted/30 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Model</p>
              <p className="mt-1 text-sm font-medium text-foreground">{model}</p>
              <p className="mt-2 text-sm text-muted-foreground">
                The backend maps this business model key to the private provider endpoint.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
              <Button type="button" variant="outline" onClick={clearConversation}>
                <Eraser className="h-4 w-4" aria-hidden="true" />
                Clear
              </Button>
              <Button type="button" variant="secondary" onClick={newConversation}>
                <Plus className="h-4 w-4" aria-hidden="true" />
                New Conversation
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="min-h-[640px]">
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <CardTitle>Conversation</CardTitle>
                <CardDescription>
                  {streaming ? "Streaming response from the model service." : "Send a message to start a chat."}
                </CardDescription>
              </div>
              <span className="rounded-md border bg-background px-3 py-1 text-sm font-medium text-foreground">
                {streaming ? "Streaming" : sending ? "Sending" : "Ready"}
              </span>
            </div>
          </CardHeader>
          <CardContent className="flex min-h-[520px] flex-col gap-4">
            <div className="flex-1 space-y-4 rounded-lg border bg-muted/20 p-4">
              {messages.length === 0 ? (
                <div className="flex h-full min-h-80 items-center justify-center text-center">
                  <div className="max-w-md space-y-3">
                    <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Bot className="h-5 w-5" aria-hidden="true" />
                    </div>
                    <p className="text-sm leading-6 text-muted-foreground">
                      Choose a role, ask a question, and AI Studio will stream the answer through the LLM Gateway.
                    </p>
                  </div>
                </div>
              ) : (
                messages.map((message, index) => (
                  <div
                    key={`${message.role}-${index}`}
                    className={message.role === "user" ? "flex justify-end" : "flex justify-start"}
                  >
                    <div
                      className={
                        message.role === "user"
                          ? "max-w-[82%] rounded-lg bg-primary px-4 py-3 text-sm leading-6 text-primary-foreground"
                          : "max-w-[82%] rounded-lg border bg-card px-4 py-3 text-sm leading-6 text-card-foreground"
                      }
                    >
                      <p className="mb-1 text-xs font-medium uppercase tracking-wide opacity-70">
                        {message.role === "user" ? "You" : "AI Studio"}
                      </p>
                      <div className="whitespace-pre-wrap">{message.content || "..."}</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {error ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            ) : null}

            <form className="space-y-3" onSubmit={handleSubmit}>
              <Label htmlFor="message">Message</Label>
              <Textarea
                id="message"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask about ComfyUI, FaceFusion, interview preparation, or general AI engineering..."
                rows={4}
                disabled={sending}
              />
              <div className="flex flex-wrap gap-3">
                <Button disabled={!canSend} type="submit">
                  <Send className="h-4 w-4" aria-hidden="true" />
                  Send
                </Button>
                <Button disabled={!streaming} type="button" variant="outline" onClick={stopGeneration}>
                  <Square className="h-4 w-4" aria-hidden="true" />
                  Stop
                </Button>
                <div className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
                  <MessageSquare className="h-4 w-4" aria-hidden="true" />
                  {messages.length} messages
                </div>
              </div>
            </form>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}

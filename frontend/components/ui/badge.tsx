import * as React from "react";

import { cn } from "@/lib/utils";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: "default" | "success" | "warning" | "danger" | "muted";
}

const toneClassName = {
  default: "border-primary/30 bg-primary/10 text-primary",
  success: "border-secondary/30 bg-secondary/10 text-secondary",
  warning: "border-amber-500/30 bg-amber-500/10 text-amber-700",
  danger: "border-destructive/30 bg-destructive/10 text-destructive",
  muted: "border-border bg-muted text-muted-foreground",
};

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium capitalize",
        toneClassName[tone],
        className,
      )}
      {...props}
    />
  );
}

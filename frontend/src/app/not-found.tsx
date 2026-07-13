"use client";

import React from "react";
import Link from "next/link";
import { FileQuestion, Home } from "lucide-react";

export default function NotFound() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#090d16] px-4">
      <div className="w-full max-w-md bg-[#111827] border border-[#1f2937] p-8 rounded-lg space-y-6 text-center">
        <div className="mx-auto h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
          <FileQuestion size={24} />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            404 - Page Not Found
          </h1>
          <p className="text-xs text-muted-foreground">
            The requested module does not exist or has been relocated in the stadium command panel.
          </p>
        </div>
        <Link
          href="/"
          className="inline-flex w-full items-center justify-center gap-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all"
        >
          <Home size={14} />
          <span>Return to Dashboard</span>
        </Link>
      </div>
    </div>
  );
}

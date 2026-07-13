"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, ArrowRight } from "lucide-react";

export default function SessionExpiredPage() {
  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#090d16] px-4">
      <div className="w-full max-w-md bg-[#111827] border border-[#1f2937] p-8 rounded-lg space-y-6 text-center">
        <div className="mx-auto h-12 w-12 rounded-full bg-red-500/10 flex items-center justify-center text-red-500">
          <ShieldAlert size={24} />
        </div>
        <div className="space-y-2">
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Session Expired
          </h1>
          <p className="text-xs text-muted-foreground">
            Your connection timed out due to inactivity or your session was terminated from another tab.
          </p>
        </div>
        <Link
          href="/login"
          className="inline-flex w-full items-center justify-center gap-2 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all"
        >
          <span>Return to login</span>
          <ArrowRight size={14} />
        </Link>
      </div>
    </div>
  );
}

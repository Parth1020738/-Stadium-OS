/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { Shield, Loader2, AlertCircle } from "lucide-react";

const resetSchema = z
  .object({
    password: z.string().min(6, { message: "Password must be at least 6 characters" }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type ResetFields = z.infer<typeof resetSchema>;

export default function ResetPasswordPage() {
  const router = useRouter();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetFields>({
    resolver: zodResolver(resetSchema),
  });

  const onSubmit = async (data: ResetFields) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);
    try {
      // Mock submit code
      setSuccessMsg("Password reset successfully. Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: any) {
      console.error(err);
      setErrorMsg("Failed to reset password. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#090d16] px-4">
      <div className="w-full max-w-md bg-[#111827] border border-[#1f2937] p-8 rounded-lg space-y-6">
        
        {/* Header Title */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            <Shield size={24} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Set New Password
          </h1>
          <p className="text-xs text-muted-foreground">
            Please enter your new security password
          </p>
        </div>

        {errorMsg && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-red-500 text-xs flex items-center gap-2">
            <AlertCircle size={14} className="flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}
        {successMsg && (
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-emerald-500 text-xs">
            {successMsg}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              New Password
            </label>
            <input
              type="password"
              disabled={isLoading}
              placeholder="••••••••"
              {...register("password")}
              className={`w-full px-3 py-2 bg-background border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary ${
                errors.password ? "border-red-500" : "border-border"
              }`}
            />
            {errors.password && (
              <span className="text-[10px] text-red-500 font-medium block">
                {errors.password.message}
              </span>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              Confirm New Password
            </label>
            <input
              type="password"
              disabled={isLoading}
              placeholder="••••••••"
              {...register("confirmPassword")}
              className={`w-full px-3 py-2 bg-background border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary ${
                errors.confirmPassword ? "border-red-500" : "border-border"
              }`}
            />
            {errors.confirmPassword && (
              <span className="text-[10px] text-red-500 font-medium block">
                {errors.confirmPassword.message}
              </span>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 size={14} className="animate-spin" />}
            <span>Reset Password</span>
          </button>
        </form>
      </div>
    </div>
  );
}

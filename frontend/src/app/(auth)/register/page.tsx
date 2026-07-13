/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { Shield, Loader2, AlertCircle } from "lucide-react";

// Registration Form schema
const registerSchema = z
  .object({
    email: z.string().email({ message: "Invalid email format" }),
    password: z.string().min(6, { message: "Password must be at least 6 characters" }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type RegisterFields = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const router = useRouter();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFields>({
    resolver: zodResolver(registerSchema),
  });

  const onSubmit = async (data: RegisterFields) => {
    setErrorMsg(null);
    setSuccessMsg(null);
    setIsLoading(true);
    try {
      await apiClient.post("/auth/register", {
        email: data.email,
        password: data.password,
      });

      setSuccessMsg("Registration successful! Redirecting to login...");
      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err.response?.data?.detail || "Registration failed. Email might already be taken."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#090d16] px-4">
      <div className="w-full max-w-md bg-[#111827] border border-[#1f2937] p-8 rounded-lg space-y-6">
        
        {/* Title Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
            <Shield size={24} />
          </div>
          <h1 className="text-xl font-bold tracking-tight text-foreground">
            Operator Registration
          </h1>
          <p className="text-xs text-muted-foreground">
            Create your Aegis Stadium Operator profile
          </p>
        </div>

        {/* Status Alerts */}
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

        {/* Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              Email Address
            </label>
            <input
              type="email"
              disabled={isLoading}
              placeholder="operator@stadium.aegis.com"
              {...register("email")}
              className={`w-full px-3 py-2 bg-background border rounded text-xs focus:outline-none focus:ring-1 focus:ring-primary ${
                errors.email ? "border-red-500" : "border-border"
              }`}
            />
            {errors.email && (
              <span className="text-[10px] text-red-500 font-medium block">
                {errors.email.message}
              </span>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-muted-foreground">
              Password
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
              Confirm Password
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
            <span>Register Profile</span>
          </button>
        </form>

        <div className="text-center pt-2">
          <p className="text-[10px] text-muted-foreground">
            Already registered?{" "}
            <Link href="/login" className="text-primary hover:underline font-medium">
              Sign In here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

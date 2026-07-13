/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { useAuthStore } from "@/store/authStore";
import { Shield, Loader2, AlertCircle } from "lucide-react";

// Form validation schema
const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email format" }),
  password: z.string().min(6, { message: "Password must be at least 6 characters" }),
});

type LoginFields = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFields>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFields) => {
    setErrorMsg(null);
    setIsLoading(true);
    try {
      const response = await apiClient.post("/auth/login", {
        email: data.email,
        password: data.password,
      });

      const { access_token, refresh_token } = response.data;
      login(access_token, refresh_token, data.email);
      router.push("/");
    } catch (err: any) {
      console.error(err);
      setErrorMsg(
        err.response?.data?.detail || "Invalid email or password. Please try again."
      );
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
            Aegis Smart Stadium OS
          </h1>
          <p className="text-xs text-muted-foreground">
            Sign in to access the Operations Command Center
          </p>
        </div>

        {/* Global Error Banner */}
        {errorMsg && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded text-red-500 text-xs flex items-center gap-2">
            <AlertCircle size={14} className="flex-shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="email" className="text-xs font-semibold text-muted-foreground">
              Email Address
            </label>
            <input
              id="email"
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
            <div className="flex items-center justify-between">
              <label htmlFor="password" className="text-xs font-semibold text-muted-foreground">
                Password
              </label>
              <Link
                href="/forgot-password"
                className="text-[10px] text-primary hover:underline font-medium"
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="password"
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

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary hover:bg-primary/95 text-primary-foreground font-semibold py-2 rounded text-xs transition-all flex items-center justify-center gap-2"
          >
            {isLoading && <Loader2 size={14} className="animate-spin" />}
            <span>Sign In</span>
          </button>
        </form>

        <div className="text-center pt-2">
          <p className="text-[10px] text-muted-foreground">
            Don&apos;t have an operator profile?{" "}
            <Link href="/register" className="text-primary hover:underline font-medium">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

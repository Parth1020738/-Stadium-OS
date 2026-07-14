/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
import "@testing-library/jest-dom";
import { vi } from "vitest";

const localStorageStore: Record<string, string> = {};
const localStorageMock = {
  getItem: vi.fn((key: string) => localStorageStore[key] || null),
  setItem: vi.fn((key: string, value: string) => {
    localStorageStore[key] = value.toString();
  }),
  removeItem: vi.fn((key: string) => {
    delete localStorageStore[key];
  }),
  clear: vi.fn(() => {
    Object.keys(localStorageStore).forEach((key) => {
      delete localStorageStore[key];
    });
  }),
  length: 0,
  key: vi.fn((index: number) => null),
};

if (typeof window !== "undefined") {
  Object.defineProperty(window, "localStorage", {
    value: localStorageMock,
    writable: true,
  });
}

if (typeof window !== "undefined" && !window.BroadcastChannel) {
  (window as any).BroadcastChannel = class {
    name: string;
    onmessage: ((ev: MessageEvent) => any) | null = null;
    constructor(name: string) {
      this.name = name;
    }
    postMessage(message: any) {}
    close() {}
  };
}
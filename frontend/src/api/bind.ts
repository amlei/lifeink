import type { BindStatus, PollResult } from "../community/types/bind";

export type { BindStatus, PollResult };
export type { PlatformProfile } from "../community/types/bind";

export async function checkBinding(platform: string): Promise<BindStatus> {
  const res = await fetch(`/api/bind?platform=${platform}`);
  return res.json();
}

export async function startBinding(platform: string): Promise<{ task_id: string }> {
  const res = await fetch(`/api/bind/start?platform=${platform}`, { method: "POST" });
  return res.json();
}

export async function unbind(platform: string): Promise<{ bound: boolean }> {
  const res = await fetch(`/api/bind?platform=${platform}`, { method: "DELETE" });
  return res.json();
}

export async function refreshProfile(platform: string): Promise<BindStatus> {
  const res = await fetch(`/api/bind/refresh?platform=${platform}`, { method: "POST" });
  return res.json();
}

export interface BindWsCallbacks {
  onQr: (base64: string) => void;
  onStatus: (status: PollResult["status"]) => void;
  onBound: (user_id: string, profile: PollResult["profile"] | undefined) => void;
  onFailed: (error: string) => void;
}

export function connectBindWs(platform: string, cb: BindWsCallbacks): WebSocket {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const ws = new WebSocket(`${proto}//${location.host}/api/bind/ws?platform=${platform}`);

  ws.onmessage = (e) => {
    const data: PollResult = JSON.parse(e.data);
    cb.onStatus(data.status);
    if (data.status === "pending" && data.qr_base64) cb.onQr(data.qr_base64);
    if (data.status === "bound") cb.onBound(data.user_id!, data.profile ?? undefined);
    if (data.status === "failed") cb.onFailed(data.error ?? "绑定失败");
  };

  return ws;
}

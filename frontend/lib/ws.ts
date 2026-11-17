import {
  API_BASE_URL,
} from "@/lib/api";


export function websocketUrl(
  path: string,
): string {
  const normalizedPath =
    path.startsWith("/")
      ? path
      : `/${path}`;

  const baseUrl = new URL(
    API_BASE_URL,
  );

  baseUrl.protocol =
    baseUrl.protocol === "https:"
      ? "wss:"
      : "ws:";

  return `${baseUrl.origin}${normalizedPath}`;
}

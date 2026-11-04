/** Decide whether this build should offer the local-only live audit. */

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1", "0.0.0.0"]);

export function isStaticDemo(hostname: string, apiUrl: string | undefined): boolean {
  if (apiUrl !== undefined && apiUrl.trim() !== "") return false;
  if (hostname === "") return false;
  return !LOCAL_HOSTS.has(hostname);
}

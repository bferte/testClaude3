/**
 * Minimal in-memory rate limiter (per server instance).
 * With several replicas, each one has its own counters: use a shared store
 * (Redis...) if the application is scaled horizontally.
 */
const hits = new Map<string, number[]>();

export function isRateLimited(key: string, max: number, windowMs: number) {
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((time) => now - time < windowMs);

  if (recent.length >= max) {
    hits.set(key, recent);
    return true;
  }

  recent.push(now);
  hits.set(key, recent);

  // Avoid unbounded growth.
  if (hits.size > 10000) {
    hits.forEach((times, k) => {
      if (times.every((time) => now - time >= windowMs)) hits.delete(k);
    });
  }

  return false;
}

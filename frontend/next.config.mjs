/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The Docker image ships the self-contained server: frontend/Dockerfile
  // copies `.next/standalone` and runs `server.js`, which requires
  // `output: "standalone"`. Vercel manages its own output, so keep this
  // opt-in: the Dockerfile sets NEXT_STANDALONE=1 at build time.
  ...(process.env.NEXT_STANDALONE === "1" ? { output: "standalone" } : {}),
};

export default nextConfig;

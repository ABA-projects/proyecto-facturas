import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    // INTERNAL_API_URL → Docker/Railway internal URL (e.g. http://api:8000)
    // Falls back to NEXT_PUBLIC_API_URL or localhost for local dev without docker
    const api = (
      process.env.INTERNAL_API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      "http://localhost:8000"
    ).trim();
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${api}/:path*`,
      },
    ];
  },
};

export default nextConfig;

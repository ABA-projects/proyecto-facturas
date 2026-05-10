import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    INTERNAL_API_URL:
      process.env.INTERNAL_API_URL ?? "http://api:8000",
  },
};

export default nextConfig;

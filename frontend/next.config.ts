import type { NextConfig } from "next";

const apiBaseUrl = process.env.AI_STUDIO_API_BASE_URL ?? "http://127.0.0.1:8002";

const nextConfig: NextConfig = {
  // Keep development assets isolated from `next build`, which otherwise
  // overwrites a running dev server's CSS and manifests in `.next`.
  distDir: process.env.NODE_ENV === "development" ? ".next-dev" : ".next",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${apiBaseUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;

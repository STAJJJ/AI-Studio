import type { NextConfig } from "next";

const apiBaseUrl = process.env.AI_STUDIO_API_BASE_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
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

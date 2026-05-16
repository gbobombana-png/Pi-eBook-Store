/** @type {import('next').NextConfig} */
const BACKEND = process.env.NEXT_PUBLIC_API_URL || "https://pi-ebook-store-production.up.railway.app";

const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_URL: BACKEND,
  },
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND}/api/v1/:path*`,
      },
    ];
  },
};
module.exports = nextConfig;

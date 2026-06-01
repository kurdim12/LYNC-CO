/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export → produces ./out, deployable as static assets on Cloudflare Pages.
  // The bot (WebRTC + ML) is a SEPARATE service; the browser connects to it directly
  // via NEXT_PUBLIC_BOT_URL. No server runtime is needed here.
  output: "export",
  // Required for static export (no Next image optimization server).
  images: { unoptimized: true },
  // Serve /operator as /operator/index.html cleanly on static hosts.
  trailingSlash: true,
};

export default nextConfig;

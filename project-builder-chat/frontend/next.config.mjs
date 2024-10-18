/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,
    assetPrefix: process.env.NODE_ENV === 'production' ? '/verbose-guacamole-qvv6jjw55xrcx5x4/' : '',
    basePath: process.env.NODE_ENV === 'production' ? '/verbose-guacamole-qvv6jjw55xrcx5x4' : '',
}

export default nextConfig
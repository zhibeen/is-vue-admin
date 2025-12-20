import { defineConfig } from '@vben/vite-config';

export default defineConfig(async () => {
  return {
    application: {},
    vite: {
      server: {
        proxy: {
          '/api': {
            changeOrigin: true,
            // 我们的 Python 后端就是以 /api 开头的，所以不需要 rewrite 去掉它
            target: 'http://localhost:5000', 
            ws: true,
          },
        },
      },
    },
  };
});

const react = require('@vitejs/plugin-react');
const basicSsl = require('@vitejs/plugin-basic-ssl');

module.exports = {
  plugins: [basicSsl(), react()],
  server: {
    port: 443,
    strictPort: true,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
};

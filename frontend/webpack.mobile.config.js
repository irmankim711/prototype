const path = require('path');
const { InjectManifest } = require('workbox-webpack-plugin');

module.exports = {
  // Mobile-specific optimizations
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        mobile: {
          test: /[\\/]src[\\/]components[\\/]Mobile[\\/]/,
          name: 'mobile',
          chunks: 'all',
        }
      }
    }
  },
  plugins: [
    new InjectManifest({
      swSrc: './public/sw.js',
      swDest: 'sw.js'
    })
  ],
  resolve: {
    alias: {
      '@mobile': path.resolve(__dirname, 'src/components/Mobile')
    }
  }
};

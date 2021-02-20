const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');
const CopyPlugin = require('copy-webpack-plugin')
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

const baseStyleLoader = (env) => env === 'production' ? MiniCssExtractPlugin.loader : require.resolve('style-loader');
const devtool = (env) => env === 'production' ? 'source-map' : 'cheap-module-eval-source-map';

module.exports = (env, argv) => {
  const isProduction = env === 'production';
  return {
    entry: {
        app: path.resolve(__dirname, 'app'),
        stats: path.resolve(__dirname, 'app/stats.js')
    },
    output: {
      filename: '[name].js',
      path: path.resolve(__dirname, 'dist'),
    },
    resolve: {
      extensions: ['.jsx', '.js', '.json', '.scss', '.css'],
      modules: ['node_modules'],
    },
    plugins: [
      new MiniCssExtractPlugin(),
      new CopyPlugin({
        patterns: [
          "app/favicon.ico",
          {from: "app/images", to: "images"},
          {from: "app/fonts", to: "fonts"},
        ]
      }),
      new CleanWebpackPlugin(),
      isProduction && new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
    ].filter(Boolean),
    devServer: {
      contentBase: path.resolve(__dirname, 'dist'),
      historyApiFallback: true,
      overlay: {
        errors: true,
        warnings: false,
      },
      port: 8001,
      publicPath: '/',
      stats: {
        assets: false,
        modules: false,
        chunks: false,
      },
    },
    module: {
      rules: [
        {
          test: /\.(png|jpg|gif|svg)$/,
          use: [
            {
              loader: require.resolve('file-loader'),
              options: {},
            },
          ],
        },
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/,
          use: require.resolve('file-loader'),
        },
        {
          test: /\.(js|jsx)$/,
          exclude: /node_modules/,
          loader: require.resolve('babel-loader'),
        },
        {
          test: /\.css$/,
          loaders: [baseStyleLoader(env), require.resolve('css-loader'), require.resolve('postcss-loader')],
        },
        {
          test: /\.scss$/,
          loaders: [
            baseStyleLoader(env),
            {
              loader: require.resolve('css-loader'),
              options: {
                importLoaders: 1,
                modules: false,
                sourceMap: true,
              },
            },
            require.resolve('postcss-loader'),
              {loader: require.resolve('sass-loader'),
                options: {
                  sassOptions: {
                    precision: 8
                  },
                }
              }
          ],
        },
      ],
    },
    devtool: devtool(env),
  };
};

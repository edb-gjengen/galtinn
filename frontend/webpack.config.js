const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const { IgnorePlugin } = require('webpack');
const CopyPlugin = require('copy-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');

const baseStyleLoader = (production) => (production ? MiniCssExtractPlugin.loader : require.resolve('style-loader'));

module.exports = ({ production }, argv) => {
    return {
        entry: {
            app: path.resolve(__dirname, 'app'),
            stats: path.resolve(__dirname, 'app/stats.js'),
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
                patterns: ['app/favicon.ico', { from: 'app/images', to: 'images' }, { from: 'app/fonts', to: 'fonts' }],
            }),
            new CleanWebpackPlugin(),
            production && new IgnorePlugin({ resourceRegExp: /^\.\/locale$/, contextRegExp: /moment$/ }),
        ].filter(Boolean),
        devServer: {
            static: path.resolve(__dirname, 'dist'),
            historyApiFallback: true,
            port: 8001,
        },
        module: {
            rules: [
                {
                    test: /\.(png|jpg|gif|svg|woff|woff2|eot|ttf|otf)$/,
                    type: 'asset/resource',
                },
                {
                    test: /\.(js|jsx)$/,
                    exclude: /node_modules/,
                    loader: require.resolve('babel-loader'),
                },
                {
                    test: /\.css$/,
                    use: [
                        baseStyleLoader(production),
                        require.resolve('css-loader'),
                        require.resolve('postcss-loader'),
                    ],
                },
                {
                    test: /\.scss$/,
                    use: [
                        baseStyleLoader(production),
                        {
                            loader: require.resolve('css-loader'),
                            options: {
                                importLoaders: 1,
                                modules: false,
                                sourceMap: true,
                            },
                        },
                        require.resolve('postcss-loader'),
                        {
                            loader: require.resolve('sass-loader'),
                            options: {
                                sassOptions: {
                                    precision: 8,
                                    loadPaths: ['.'],
                                    silenceDeprecations: [
                                        'import',
                                        'mixed-decls',
                                        'color-functions',
                                        'global-builtin',
                                        'legacy-js-api',
                                    ],
                                },
                            },
                        },
                    ],
                },
            ],
        },
        devtool: production ? 'source-map' : 'cheap-module-source-map',
    };
};

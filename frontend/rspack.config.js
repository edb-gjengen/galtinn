const path = require('path');
const { rspack } = require('@rspack/core');

module.exports = ({ production }, argv) => {
    return {
        entry: {
            app: path.resolve(__dirname, 'app'),
            stats: path.resolve(__dirname, 'app/stats.js'),
        },
        output: {
            clean: true,
            filename: '[name].js',
            path: path.resolve(__dirname, 'dist'),
        },
        resolve: {
            extensions: ['.jsx', '.js', '.json', '.scss', '.css'],
            modules: ['node_modules'],
        },
        plugins: [
            new rspack.CssExtractRspackPlugin(),
            new rspack.CopyRspackPlugin({
                patterns: ['app/favicon.ico', { from: 'app/images', to: 'images' }, { from: 'app/fonts', to: 'fonts' }],
            }),
            production && new rspack.IgnorePlugin({ resourceRegExp: /^\.\/locale$/, contextRegExp: /moment$/ }),
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
                    loader: 'builtin:swc-loader',
                },
                {
                    test: /\.css$/,
                    use: [
                        rspack.CssExtractRspackPlugin.loader,
                        require.resolve('css-loader'),
                        require.resolve('postcss-loader'),
                    ],
                    type: 'javascript/auto',
                },
                {
                    test: /\.scss$/,
                    use: [
                        rspack.CssExtractRspackPlugin.loader,
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

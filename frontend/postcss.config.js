module.exports = {
    plugins: [
        require('autoprefixer'),
        // svgo cannot parse the percent-encoded inline SVGs sass writes for Bootstrap's icons, which are minified already
        require('cssnano')({ preset: ['default', { svgo: false }] }),
    ],
};

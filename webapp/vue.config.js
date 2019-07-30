module.exports = {
    chainWebpack: config => {
        const svgRule = config.module.rule('svg')

        // clear all existing loaders.
        // if you don't do this, the loader below will be appended to
        // existing loaders of the rule.
        svgRule.uses.clear()

        // add replacement loader(s)
        svgRule
        .use('vue-svg-loader')
            .loader('vue-svg-loader')
    },

    devServer: {
        proxy: {
            '/socket.io/*': {
            // pathRewrite: {'^/socket.io': ''},
            // target: 'http://0.0.0.0:9090/',
            target: 'http://localhost:5000/',
            secure: false,
            changeOrigin: true,
            ws: true,
            //logLevel: 'debug',
            },
            'get_random_class_image/*': {
            // pathRewrite: {'^/socket.io': ''},
                target: 'http://localhost:5000/',
                secure: false,
                changeOrigin: true,
    
            }
        }
    }
}
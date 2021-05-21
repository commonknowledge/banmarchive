const path = require("path");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

module.exports = (env) => {
  /** @type {import("webpack").WebpackOptionsNormalized } */
  return {
    mode: env.production ? "production" : "development",
    entry: ["./banmarchive/scss/index.scss"],
    devtool: "eval-source-map",

    module: {
      rules: [
        {
          test: /\.(png|svg|jpg|jpeg|gif)$/i,
          type: "asset/resource",
        },
        {
          test: /\.(scss)$/,
          use: [
            {
              // inject CSS to page
              loader: env.production
                ? MiniCssExtractPlugin.loader
                : "style-loader",
            },
            {
              // translates CSS into CommonJS modules
              loader: "css-loader",
            },
            {
              // Run postcss actions
              loader: "postcss-loader",
              options: {
                postcssOptions: {
                  plugins: function () {
                    return [require("autoprefixer")];
                  },
                },
              },
            },
            {
              loader: "sass-loader",
            },
          ],
        },
      ],
    },
    plugins: [],

    plugins: [
      ...(env.production
        ? [
            new MiniCssExtractPlugin({ filename: "[name].[hash].css" }),
            new BundleTracker({
              path: __dirname,
              filename: "./dist/webpack-stats.json",
            }),
          ]
        : []),
    ],

    output: {
      ...(env.production
        ? {
            filename: "[name]-[hash].js",
            chunkFilename: "[id].[chunkhash].js",
          }
        : {
            filename: "[name].js",
            chunkFilename: "[id].js",
          }),
      path: path.resolve(__dirname, "dist"),
      pathinfo: false,
    },
  };
};

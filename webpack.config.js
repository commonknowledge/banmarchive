const path = require("path");
const BundleTracker = require("webpack-bundle-tracker");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

const isProduction = process.env.NODE_ENV === "production";

/** @type {import("webpack").WebpackOptionsNormalized } */
module.exports = {
  mode: isProduction ? "production" : "development",
  entry: {
    main: ["./banmarchive/scss/index.scss"],
    pdf: ["./publications/js/pdf.js", "./publications/scss/pdf.scss"]
  },
  devtool: isProduction ? "eval-source-map" : false,

  module: {
    rules: [
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: "asset/resource",
      },
      {
        test: /\.jsx?/,
        use: [
          {
            loader: "babel-loader",
          },
        ]
      },
      {
        test: /\.(scss)$/,
        use: [
          {
            // inject CSS to page
            loader: isProduction ? MiniCssExtractPlugin.loader : "style-loader",
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
      {
        test: /\.(css)$/,
        use: [
          {
            // inject CSS to page
            loader: isProduction ? MiniCssExtractPlugin.loader : "style-loader",
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
        ],
      },
    ],
  },

  devServer: {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
      "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization"
    }  
  },

  plugins: [
    ...(isProduction
      ? [
          new MiniCssExtractPlugin({
            filename: "[name].css",
            chunkFilename: "[id].css",
          }),
          new BundleTracker({
            path: __dirname,
            filename: "./dist/webpack-stats.json",
          }),
        ]
      : []),
  ],

  output: {
    filename: "[name].js",
    chunkFilename: "[id].js",
    path: path.resolve(__dirname, "dist"),
    pathinfo: false,
  },
};

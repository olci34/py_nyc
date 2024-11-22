const { watch } = require("fs");
const path = require("path");

module.exports = {
  entry: "./js/index.js", // Your entry file
  output: {
    filename: "bundle.js", // Output bundle file
    path: path.resolve(__dirname, "dist"), // Output directory
    publicPath: "/static/dist/",
  },
  mode: "development", // Change to 'production' for production build
  module: {
    rules: [
      {
        test: /\.css$/, // Handle CSS files
        use: ["style-loader", "css-loader"],
      },
    ],
  },
  watch: true,
};

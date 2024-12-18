const path = require('path');

module.exports = {
  entry: './src/index.js',  // точка входа в ваше приложение
  output: {
    filename: 'main.js',
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js'
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/, // обработка .js и .jsx файлов
        exclude: /node_modules/, // исключаем node_modules
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env', '@babel/preset-react'],
          },
        },
      },
      {
        test: /\.css$/,  // обработка .css файлов
        use: ['style-loader', 'css-loader'], // сначала css-loader, потом style-loader
      },
    ],
  },
  resolve: {
    extensions: ['.js', '.jsx'], // добавляем расширения .js и .jsx
  },
  devServer: {
    static: {
      directory: path.join(__dirname, 'public'),  // заменяем contentBase на static и указываем директорию src
    },
    compress: true,
    port: 8081,
    open: true,  // автоматически открывает браузер
  },
};

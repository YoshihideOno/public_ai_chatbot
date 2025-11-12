import resolve from '@rollup/plugin-node-resolve';
import commonjs from '@rollup/plugin-commonjs';
import babel from '@rollup/plugin-babel';
import terser from '@rollup/plugin-terser';

export default {
  input: 'src/index.js',
  output: {
    file: 'dist/widget.js',
    format: 'iife',
    name: 'RagChatWidget',
    compact: true
  },
  plugins: [
    resolve(),
    commonjs(),
    babel({
      babelHelpers: 'bundled',
      presets: [
        ['@babel/preset-env', { targets: '> 0.5%, not dead, not ie 11' }]
      ]
    }),
    terser({
      compress: { drop_console: true, passes: 2 }
    })
  ]
}



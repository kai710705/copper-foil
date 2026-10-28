module.exports = {
  content: ['../app/templates/**/*.html', '../app/static/js/**/*.js'],
  corePlugins: { preflight: false },
  theme: { extend: { backdropBlur: { glass: '18px' } } },
  plugins: []
};

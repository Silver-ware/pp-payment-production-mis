module.exports = {
    content: [
        '../templates/**/*.html',
        '../../templates/**/*.html',
        '../../**/templates/**/*.html',
    ],
    theme: {
        extend: {
            textStroke: {
                'green': '2px #006400', // Dark Green Stroke
            }
        },
    },
    plugins: [
        function ({ addUtilities }) {
            addUtilities({
              '.text-stroke-green': {
                '-webkit-text-stroke': '2px #006400',
                'text-stroke': '2px #006400',
              }
            });
        },
        require('tailwind-scrollbar'),
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}

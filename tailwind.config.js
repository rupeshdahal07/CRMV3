/**
 * Nobigo CRM — global design system.
 *
 * This file is the single source of truth for the theme (colours, radii,
 * shadows, typography) taken from the approved UI design. Templates use the
 * semantic utility names below (e.g. `bg-brand`, `text-ink`, `shadow-card`)
 * and the component classes defined in `theme/input.css`.
 */
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/*.py', // class strings built in Python (badges, dynamic styles)
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#ecedf1', // app background
        surface: '#ffffff', // cards / panels
        sidebar: '#fbfbfd',
        ink: {
          DEFAULT: '#17171c', // primary text / dark buttons
          soft: '#3a3a44',
          mute: '#5b6472',
        },
        brand: {
          DEFAULT: '#6d5efc',
          400: '#7c6bff',
          500: '#7c6bff',
          600: '#6d5efc',
          soft: '#efedff', // tinted background for brand chips/nav
          softer: '#f4f2ff',
        },
        success: { DEFAULT: '#1f9d57', soft: '#e9f7ef' },
        danger: { DEFAULT: '#e5484d', soft: '#fdecec' },
        amber: { DEFAULT: '#d98324', soft: '#fdf1e3' },
        accent: { DEFAULT: '#e5734d' },
        muted: {
          DEFAULT: '#9aa1ad',
          strong: '#6b7280',
          faint: '#a4abb7',
          soft: '#8b93a1',
        },
        chip: '#f1f2f6',
        line: {
          DEFAULT: '#edeef3',
          soft: '#f4f5f8',
          strong: '#e6e8ee',
          input: '#e0e2e9',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        card: '16px',
        shell: '22px',
      },
      boxShadow: {
        card: '0 1px 2px rgba(17,17,26,.04)',
        lift: '0 18px 34px -14px rgba(109,94,252,.35), 0 2px 6px rgba(17,17,26,.06)',
        shell: '0 24px 60px -30px rgba(23,23,28,.28), 0 2px 8px rgba(23,23,28,.05)',
        focus: '0 0 0 5px rgba(109,94,252,.16)',
      },
      backgroundImage: {
        'brand-grad': 'linear-gradient(135deg,#7c6bff,#6d5efc)',
        'ink-grad': 'linear-gradient(135deg,#2a2a33,#17171c)',
        'podium-grad': 'linear-gradient(160deg,#7c6bff,#6d5efc)',
      },
      keyframes: {
        rise: {
          from: { opacity: '0', transform: 'translateY(14px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        rise: 'rise .45s cubic-bezier(.2,.7,.2,1) both',
      },
      maxWidth: {
        content: '1240px',
      },
    },
  },
  plugins: [],
};

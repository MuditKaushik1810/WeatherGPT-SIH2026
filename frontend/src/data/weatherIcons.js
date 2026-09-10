import { createElement } from 'react'

const svg = (children) =>
  createElement(
    'svg',
    {
      viewBox: '0 0 40 40',
      width: 32,
      height: 32,
      fill: 'none',
      'aria-hidden': 'true',
    },
    children
  )

const icons = {
  sun: svg([
    createElement('circle', { key: 'glow', cx: 20, cy: 20, r: 10, fill: '#F8C96B', opacity: 0.25 }),
    createElement('circle', { key: 'sun', cx: 20, cy: 20, r: 7.5, fill: '#F6C85F' }),
    createElement('circle', { key: 'shine', cx: 17.5, cy: 17, r: 2.2, fill: '#FFE9A8', opacity: 0.9 }),
    ...Array.from({ length: 8 }, (_, i) => {
      const a = (i * Math.PI) / 4
      return createElement('line', {
        key: `ray-${i}`,
        x1: 20 + Math.cos(a) * 11,
        y1: 20 + Math.sin(a) * 11,
        x2: 20 + Math.cos(a) * 14,
        y2: 20 + Math.sin(a) * 14,
        stroke: '#E9B84F',
        strokeWidth: 2.4,
        strokeLinecap: 'round',
      })
    }),
  ]),

  partlyCloudy: svg([
    createElement('circle', { key: 'sun', cx: 13, cy: 14, r: 6, fill: '#F6C85F' }),
    createElement('circle', { key: 'shine', cx: 11.5, cy: 12.5, r: 1.8, fill: '#FFE9A8' }),
    createElement('path', {
      key: 'cloud-shadow',
      d: 'M10 30h19a6 6 0 0 0 .5-12 8 8 0 0 0-15.4-2A6.5 6.5 0 0 0 10 30Z',
      fill: '#B8CBE0',
    }),
    createElement('path', {
      key: 'cloud',
      d: 'M10 28h19a6 6 0 0 0 .5-12 8 8 0 0 0-15.4-2A6.5 6.5 0 0 0 10 28Z',
      fill: '#DCE8F2',
    }),
    createElement('ellipse', {
      key: 'highlight',
      cx: 20,
      cy: 20,
      rx: 7,
      ry: 3,
      fill: '#F5FAFD',
      opacity: 0.7,
    }),
  ]),

  cloud: svg([
    createElement('path', {
      key: 'shadow',
      d: 'M7 30h25a7 7 0 0 0 .5-14 9 9 0 0 0-17.3-2.2A7.5 7.5 0 0 0 7 30Z',
      fill: '#AFC4D8',
    }),
    createElement('path', {
      key: 'cloud',
      d: 'M7 28h25a7 7 0 0 0 .5-14 9 9 0 0 0-17.3-2.2A7.5 7.5 0 0 0 7 28Z',
      fill: '#D9E6F0',
    }),
    createElement('ellipse', {
      key: 'highlight',
      cx: 20,
      cy: 19,
      rx: 9,
      ry: 4,
      fill: '#F6FAFD',
      opacity: 0.8,
    }),
  ]),

  fog: svg([
    createElement('path', {
      key: 'cloud',
      d: 'M8 21h24a6 6 0 0 0 .4-12 8 8 0 0 0-15.3-2A6.5 6.5 0 0 0 8 21Z',
      fill: '#D7E2EA',
    }),
    createElement('rect', { key: 'f1', x: 7, y: 24, width: 26, height: 3, rx: 1.5, fill: '#AFC4D4' }),
    createElement('rect', { key: 'f2', x: 11, y: 30, width: 19, height: 3, rx: 1.5, fill: '#C4D5E1' }),
  ]),

  drizzle: svg([
    createElement('path', {
      key: 'cloud',
      d: 'M7 22h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 22Z',
      fill: '#CFDFEA',
    }),
    createElement('ellipse', { key: 'highlight', cx: 20, cy: 15, rx: 8, ry: 3, fill: '#F5FAFD', opacity: 0.75 }),
    createElement('circle', { key: 'd1', cx: 12, cy: 28, r: 2, fill: '#83BBD5' }),
    createElement('circle', { key: 'd2', cx: 20, cy: 30, r: 2, fill: '#83BBD5' }),
    createElement('circle', { key: 'd3', cx: 28, cy: 28, r: 2, fill: '#83BBD5' }),
  ]),

  rain: svg([
    createElement('path', {
      key: 'shadow',
      d: 'M7 21h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 21Z',
      fill: '#AFC4D8',
    }),
    createElement('path', {
      key: 'cloud',
      d: 'M7 19h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 19Z',
      fill: '#D5E3ED',
    }),
    createElement('ellipse', { key: 'highlight', cx: 20, cy: 11, rx: 8, ry: 3, fill: '#F5FAFD', opacity: 0.8 }),
    createElement('path', { key: 'r1', d: 'M12 25l-2 6', stroke: '#71B4D4', strokeWidth: 3.2, strokeLinecap: 'round' }),
    createElement('path', { key: 'r2', d: 'M20 25l-2 7', stroke: '#5FA9CC', strokeWidth: 3.2, strokeLinecap: 'round' }),
    createElement('path', { key: 'r3', d: 'M28 25l-2 6', stroke: '#71B4D4', strokeWidth: 3.2, strokeLinecap: 'round' }),
  ]),

  snow: svg([
    createElement('path', {
      key: 'cloud',
      d: 'M7 20h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 20Z',
      fill: '#D8E5EF',
    }),
    createElement('ellipse', { key: 'highlight', cx: 20, cy: 12, rx: 8, ry: 3, fill: '#F7FBFD', opacity: 0.8 }),
    ...[
      [12, 27],
      [20, 31],
      [28, 27],
    ].map(([cx, cy], i) =>
      createElement('circle', {
        key: `snow-${i}`,
        cx,
        cy,
        r: 3,
        fill: '#9CCFE5',
      })
    ),
    createElement('circle', { key: 'shine1', cx: 11, cy: 26, r: 0.9, fill: '#EAF7FC' }),
    createElement('circle', { key: 'shine2', cx: 19, cy: 30, r: 0.9, fill: '#EAF7FC' }),
  ]),

  storm: svg([
    createElement('path', {
      key: 'shadow',
      d: 'M7 20h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 20Z',
      fill: '#899FB8',
    }),
    createElement('path', {
      key: 'cloud',
      d: 'M7 18h25a6 6 0 0 0 .5-12 9 9 0 0 0-17.3-2.2A7 7 0 0 0 7 18Z',
      fill: '#AFC0D1',
    }),
    createElement('ellipse', { key: 'highlight', cx: 20, cy: 10, rx: 8, ry: 3, fill: '#DDE8F1', opacity: 0.8 }),
    createElement('path', {
      key: 'bolt-shadow',
      d: 'M21 18l-8 12h6l-2 8 10-14h-6l4-6Z',
      fill: '#DDAF43',
    }),
    createElement('path', {
      key: 'bolt',
      d: 'M21 17l-8 12h6l-2 8 10-14h-6l4-6Z',
      fill: '#F5C957',
    }),
  ]),
}

export function getWeatherIcon(condition) {
  const value = String(condition ?? '').trim().toLowerCase()

  if (!value || value === 'unknown') return null
  if (value.includes('thunder') || value.includes('storm')) return icons.storm
  if (value.includes('hail')) return icons.storm
  if (value.includes('snow')) return icons.snow
  if (value.includes('drizzle')) return icons.drizzle
  if (value.includes('rain') || value.includes('shower')) return icons.rain
  if (value.includes('fog') || value.includes('mist')) return icons.fog
  if (value.includes('partly') && value.includes('cloud')) return icons.partlyCloudy
  if (value.includes('cloud') || value.includes('overcast')) return icons.cloud
  if (value.includes('clear') || value.includes('sunny') || value === 'mainly clear') return icons.sun

  return null
}

export const weatherIcons = icons

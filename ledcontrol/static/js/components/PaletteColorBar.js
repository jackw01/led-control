// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

export default {
  props: {
    'colors': Array,
  },
  mounted() {
    const c = this.$refs['canvas'];
    const ctx = c.getContext('2d');
    c.width = 32;
    c.height = 1;
    const sectorSize = 1 / (this.colors.length - 1);
    for (let i = 0; i < c.width; i++) {
      let f = i / c.width;
      const sector = Math.floor(f / sectorSize);
      f = f % sectorSize / sectorSize;
      const c1 = this.colors[sector];
      const c2 = this.colors[sector + 1];
      let h1 = c2[0] - c1[0];
      // Allow full spectrum if extremes are 0 and 1 in any order
      // otherwise pick shortest path between colors
      if (Math.abs(h1) != 1) {
        if (h1 < -0.5) h1++;
        if (h1 > 0.5) h1--;
      }
      const h = (f * h1 + c1[0]) * 360;
      const s = (f * (c2[1] - c1[1]) + c1[1]) * 100;
      const v = (f * (c2[2] - c1[2]) + c1[2]) * 100;
      const l = (2 - s / 100) * v / 2;
      const s2 = s * v / (l < 50 ? l * 2 : 200 - l * 2);
      ctx.fillStyle = `hsl(${h}, ${s}%, ${l}%)`
      ctx.fillRect(i, 0, 1, c.height);
    }
  },
  template: `
    <canvas ref="canvas" style="display: block; border-radius: 3px; width: 100%; height: 0.7rem; margin-bottom: 0.5rem;"></canvas>
  `,
};

import store from '../Store.js';

export default {
  props: {
    'name': String,
    'i': Number,
  },
  data() {
    return {
      selectedFunction: store.get('groups.' + this.name + '.function'),
      selectedPalette: store.get('groups.' + this.name + '.palette'),
    }
  },
  computed: {
    groups: function () {
      return store.get('groups');
    },
    functions: function () {
      return store.getFunctions();
    },
    palettes: function () {
      return store.getPalettes();
    }
  },
  methods: {
    updateFunction(event) {
      store.set('groups.' + this.name + '.function', this.selectedFunction);
    },
    updatePalette(event) {
      store.set('groups.' + this.name + '.palette', this.selectedPalette);
      this.drawPalettePreview();
    },
    drawPalettePreview() {
      const c = document.getElementById('palette-color-bar');
      const ctx = c.getContext('2d');
      c.width = 64;
      c.height = 1;
      const sectorSize = 1 / (this.palettes[this.selectedPalette].colors.length - 1);
      for (let i = 0; i < c.width; i++) {
        let f = i / c.width;
        const sector = Math.floor(f / sectorSize);
        f = f % sectorSize / sectorSize;
        const c1 = this.palettes[this.selectedPalette].colors[sector];
        const c2 = this.palettes[this.selectedPalette].colors[sector + 1];
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
    }
  },
  mounted() {
    this.drawPalettePreview();
  },
  template: `
    <h4>Group {{ i + 1 }} ({{ name }})</h4>
      <slider-number-input
        v-bind:path="'groups.' + name + '.brightness'"
        label="Brightness"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
      <slider-number-input
        v-bind:path="'groups.' + name + '.color_temp'"
        label="Color Temp"
        unit="K"
        v-bind:min="1000"
        v-bind:max="12000"
        v-bind:step="10"
      ></slider-number-input>
      <slider-number-input
        v-bind:path="'groups.' + name + '.saturation'"
        label="Saturation"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
      <div class="input-row input-row-top-margin input-toplevel">
        <span class="label select-label">Pattern:</span>
        <span class="select-container">
          <select
            class="update-on-change"
            autocomplete="off"
            v-model="selectedFunction"
            @change="updateFunction"
          >
            <option
              v-for="(f, id) in functions"
              v-bind:value="id"
            >
              {{ f.name }}
            </option>
          </select>
        </span>
      </div>
      <slider-number-input
        v-bind:path="'groups.' + name + '.speed'"
        label="Speed"
        unit="Hz"
        v-bind:min="0"
        v-bind:max="2"
        v-bind:step="0.01"
      ></slider-number-input>
      <slider-number-input
        v-bind:path="'groups.' + name + '.scale'"
        label="Scale"
        unit=""
        v-bind:min="-10"
        v-bind:max="10"
        v-bind:step="0.01"
      ></slider-number-input>
      <div class="input-row input-row-top-margin input-toplevel">
        <span class="label select-label">Palette:</span>
        <span class="select-container">
          <select
            class="update-on-change"
            autocomplete="off"
            v-model="selectedPalette"
            @change="updatePalette"
          >
            <option
              v-for="(p, id) in palettes"
              v-bind:value="id"
            >
              {{ p.name }}
            </option>
          </select>
        </span>
      </div>
      <canvas id="palette-color-bar" style="display: block; border-radius: 3px; width: 100%; height: 0.7rem; margin-bottom: 0.5rem;"></canvas>
  `,
};

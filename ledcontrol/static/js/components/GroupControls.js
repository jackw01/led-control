// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  props: {
    'name': String,
  },
  data() {
    const functionKey = store.get('groups.' + this.name + '.function');
    const paletteKey = store.get('groups.' + this.name + '.palette');
    return {
      functionKey,
      animFunction: store.getFunctions()[functionKey],
      sourceStatus: '',
      sourceStatusClass: '',
      paletteKey,
      palette: store.getPalettes()[paletteKey],
      codeMirror: {},
      palettePreviewKey: 0,
      showPaletteList: false,
    }
  },
  computed: {
    groups: function() {
      return store.get('groups');
    },
    functions: function() {
      return store.getFunctions();
    },
    palettes: function() {
      return store.getPalettes();
    },
  },
  methods: {
    updateFunction() {
      store.set('groups.' + this.name + '.function', parseInt(this.functionKey, 10));
      this.animFunction = this.functions[this.functionKey];
      this.$nextTick(this.createCodeEditor);
    },
    async updateFunctionSource() {
      await store.setFunction(parseInt(this.functionKey, 10), this.animFunction);
    },
    newFunction() {
      const newKey = Date.now();
      const newFunction = JSON.parse(JSON.stringify(this.animFunction));
      newFunction.name = this.animFunction.name + ' (Copy)';
      newFunction.default = false;
      store.setFunction(newKey, newFunction);
      this.functionKey = newKey;
      this.updateFunction();
    },
    deleteFunction() {
      if (confirm(`Delete pattern "${this.animFunction.name}?"`)) {
        store.removeFunction(parseInt(this.functionKey, 10));
        this.functionKey = 0;
        this.updateFunction();
      }
    },
    async compileFunction() {
      const source = this.codeMirror.getValue();
      this.animFunction.source = source;
      await this.updateFunctionSource();
      const result = await store.requestCompile(parseInt(this.functionKey, 10));
      console.log('Compile errors/warnings:', result.errors, result.warnings);
      if (result.errors.length === 0) {
        this.sourceStatusClass = 'status-success';
        this.sourceStatus = 'Pattern compiled successfully';
      } else if (result.errors.length > 0) {
        this.sourceStatusClass = 'status-error';
        this.sourceStatus = result.errors.join(', ');
      }
    },
    createCodeEditor() {
      let code = this.animFunction.source.trim();
      if (this.animFunction.default) {
        code = '# Editing and renaming disabled on default patterns. Click "New Pattern" to create and edit a copy of this pattern.\n\n' + code;
      }
      this.codeMirror = new CodeMirror(this.$refs.code, {
        value: code,
        mode: 'python',
        indentUnit: 4,
        lineNumbers: true,
        lineWrapping: true,
        theme: 'summer-night',
        readOnly: this.animFunction.default,
      });
      this.codeMirror.setOption('extraKeys', {
        Tab: function(cm) {
          const spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
          cm.replaceSelection(spaces);
        }
      });
      this.sourceStatus = 'Pattern not compiled yet';
      this.sourceStatusClass = 'status-none';
    },
    updatePalette() {
      store.set('groups.' + this.name + '.palette', parseInt(this.paletteKey, 10));
      this.palette = this.palettes[this.paletteKey];
      this.palettePreviewKey++;
      this.$nextTick(this.createColorPickers);
    },
    selectPalette(id) {
      this.paletteKey = id;
      this.updatePalette();
    },
    newPalette() {
      const newKey = Date.now();
      const newPalette = JSON.parse(JSON.stringify(this.palette));
      newPalette.name = this.palette.name + ' (Copy)';
      newPalette.default = false;
      store.setPalette(newKey, newPalette);
      this.paletteKey = newKey;
      this.updatePalette();
    },
    deletePalette() {
      if (confirm(`Delete palette "${this.palette.name}?"`)) {
        store.removePalette(parseInt(this.paletteKey, 10));
        this.paletteKey = 0;
        this.updatePalette();
      }
    },
    updatePaletteContents() {
      store.setPalette(parseInt(this.paletteKey, 10), this.palette);
      this.palettePreviewKey++;
    },
    addColor(i) {
      this.palette.colors.splice(i + 1, 0, this.palette.colors[i].slice());
      this.updatePaletteContents();
      this.$nextTick(this.createColorPickers);
    },
    deleteColor(i) {
      if (this.palette.colors.length > 2) {
        this.palette.colors.splice(i, 1);
        this.updatePaletteContents();
        this.$nextTick(this.createColorPickers);
      }
    },
    togglePaletteList() {
      this.showPaletteList = !this.showPaletteList;
    },
    createColorPickers() {
      if (!this.palette.default) {
        for (let i = 0; i < this.palette.colors.length; i++) {
          const pickr = Pickr.create({
            el: `#color-picker-${i}`,
            theme: 'classic',
            showAlways: true,
            inline: true,
            lockOpacity: true,
            comparison: false,
            default: `hsv(${this.palette.colors[i][0] * 360}, ${this.palette.colors[i][1] * 100}%, ${this.palette.colors[i][2] * 100}%)`,
            swatches: null,
            components: {
              preview: false,
              opacity: false,
              hue: true,
              interaction: { hex: true, rgba: true, hsla: true, hsva: true, input: true },
            },
          });
          pickr.index = i;
          pickr.on('changestop', (c, instance) => {
            const color = instance.getColor();
            this.palette.colors[instance.index] = [
              color.h / 360, color.s / 100, color.v / 100
            ];
            this.updatePaletteContents();
          });
        }
      }
    }
  },
  mounted() {
    this.$nextTick(this.createCodeEditor);
    this.$nextTick(this.createColorPickers);
  },
  template: `
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
      v-bind:step="50"
      v-if="false"
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
          autocomplete="off"
          v-model="functionKey"
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
    <div class="input-row input-row-top-margin">
      <a
        class="button"
        @click="newFunction"
      >New Pattern</a>
      <a
        class="button"
        v-show="!animFunction.default"
        @click="deleteFunction"
      >Delete</a>
      <input
        type="text"
        v-model="animFunction.name"
        @change="updateFunctionSource"
        v-bind:disabled="animFunction.default"
        autocomplete="off"
      >
    </div>
    <div class="input-row input-row-top-margin input-row-bottom-margin">
      <span
        class="infotext"
        v-bind:class="sourceStatusClass"
      >{{ sourceStatus }}</span>
      <a
        class="button"
        @click="compileFunction"
      >Compile Pattern</a>
    </div>
    <div ref="code" :key="functionKey"></div>
    <br />
    <div class="input-row input-row-top-margin input-toplevel">
      <span class="label select-label">Palette:</span>
      <span class="select-container">
        <select
          autocomplete="off"
          v-model="paletteKey"
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
      <a
        class="button"
        @click="togglePaletteList"
        v-bind:class="{'active': showPaletteList}"
      >Show All</a>
    </div>
    <palette-color-bar
      v-bind:colors="palette.colors"
      v-if="!showPaletteList"
      :key="palettePreviewKey">
    </palette-color-bar>
    <table class="palette-list" v-if="showPaletteList">
      <tr v-for="(p, id) in palettes" @click="selectPalette(id)">
        <td>{{ p.name }}</td>
        <td>
          <palette-color-bar
            v-bind:colors="p.colors"
            :key="palettePreviewKey">
          </palette-color-bar>
        </td>
      </tr>
    </table>
    <div id="colors">
      <div class="input-row input-row-bottom-margin">
        <a
          class="button"
          @click="newPalette"
        >New Palette</a>
        <a
          class="button"
          v-show="!palette.default"
          @click="deletePalette"
        >Delete</a>
        <input
          type="text"
          v-model="palette.name"
          @change="updatePaletteContents"
          v-bind:disabled="palette.default"
          autocomplete="off"
        >
      </div>
      <div id="color-picker-container" v-if="!palette.default">
        <div
          v-for="(color, i) in palette.colors"
          :key="paletteKey + '.' + palette.colors.length + '.' + i"
        >
          <div class="input-row input-row-top-margin">
            <span class="label">Color {{ i + 1 }}:</span>
            <a
              class="button button-inline"
              v-show="!palette.default"
              @click="addColor(i)"
            >+</a>
            <a
              class="button button-inline"
              v-show="!palette.default"
              @click="deleteColor(i)"
            >-</a>
          </div>
          <span class="color-picker" v-bind:id="'color-picker-' + i"></span>
        </div>
      </div>
    </div>
  `,
};

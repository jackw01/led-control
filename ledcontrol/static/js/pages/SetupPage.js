// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  name: 'SetupPage',
  data() {
    return {
      sacn: store.get('sacn'),
    }
  },
  methods: {
    updateSACN() {
      store.set('sacn', parseInt(this.sacn, 10));
    }
  },
  template: `
    <slider-number-input
      path="global_color_temp"
      label="Global Color Temp"
      unit="K"
      v-bind:min="1000"
      v-bind:max="12000"
      v-bind:step="50"
    ></slider-number-input>
    <slider-number-input
      path="global_color_r"
      label="Color Correction (Red)"
      unit=""
      v-bind:min="0"
      v-bind:max="255"
      v-bind:step="1"
    ></slider-number-input>
    <slider-number-input
      path="global_color_g"
      label="Color Correction (Green)"
      unit=""
      v-bind:min="0"
      v-bind:max="255"
      v-bind:step="1"
    ></slider-number-input>
    <slider-number-input
      path="global_color_b"
      label="Color Correction (Blue)"
      unit=""
      v-bind:min="0"
      v-bind:max="255"
      v-bind:step="1"
    ></slider-number-input>
    <div class="input-row input-row-top-margin input-toplevel">
      <span class="label select-label">E1.31 sACN Control:</span>
      <span class="select-container">
        <select
          class="update-on-change"
          autocomplete="off"
          v-model="sacn"
          @change="updateSACN"
        >
          <option value="0">Off</option>
          <option value="1">On</option>
        </select>
      </span>
    </div>
  `,
}

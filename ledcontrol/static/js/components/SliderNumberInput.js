// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  props: {
    'path': String,
    'label': String,
    'unit': String,
    'min': Number,
    'max': Number,
    'step': Number,
  },
  data() {
    return {
      val: store.get(this.path),
    }
  },
  methods: {
    update(event) {
      store.set(this.path, _.clamp(this.val, this.min, this.max));
    }
  },
  template: `
    <div class="input-toplevel">
      <span class="label">{{ label }}:
        <span class="dim" v-if="unit.length > 0">({{ unit }})</span>
      </span>
      <div class="input-row">
        <div class="input-slider-container">
          <input
            type="range"
            :min="min"
            :max="max"
            :step="step"
            autocomplete="off"
            v-model="val"
            @change="update"
          >
        </div>
        <div class="input-number-container">
          <input
            type="number"
            style="width:80px"
            :min="min"
            :max="max"
            :step="step"
            autocomplete="off"
            v-model="val"
            @change="update"
          >
        </div>
      </div>
    </div>
  `,
};

// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  props: {
    'name': String,
  },
  data() {
    return {
      group: store.get('groups')[this.name],
    }
  },
  methods: {
    rename(event) {
      store.set(`groups[${this.name}].name`, this.group.name);
    },
    setBounds(event) {
      if (this.group.range_start < this.group.range_end) {
        const items = {};
        items[`groups[${this.name}].range_start`] = this.group.range_start;
        items[`groups[${this.name}].range_end`] = this.group.range_end;
        store.setMultiple(items);
      }
    }
  },
  template: `
    <div class="input-row input-row-top-margin input-row-bottom-margin">
      <span class="label select-label">Name:</span>
      <input
        type="text"
        autocomplete="off"
        v-model="group.name"
        @change="rename"
      >
    </div>
    <div class="input-row input-row-top-margin input-row-bottom-margin">
      <span class="label select-label">Range (LEDs):</span>
      <input
        class="input-inline"
        type="number"
        min="0"
        max="10000"
        step="1"
        autocomplete="off"
        v-model="group.range_start"
        @change="setBounds"
      >
      <span class="label select-label"> to </span>
      <input
        class="input-inline"
        type="number"
        min="0"
        max="10000"
        step="1"
        autocomplete="off"
        v-model="group.range_end"
        @change="setBounds"
      >
    </div>
  `,
};

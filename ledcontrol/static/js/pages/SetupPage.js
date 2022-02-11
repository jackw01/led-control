// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  name: 'SetupPage',
  data() {
    return {
      sacn: store.get('sacn'),
      calibration: store.get('calibration'),
      groupListKey: 0,
    }
  },
  computed: {
    groups: function() {
      return store.get('groups');
    }
  },
  methods: {
    updateSACN() {
      store.set('sacn', parseInt(this.sacn, 10));
    },
    updateCalibration() {
      store.set('calibration', parseInt(this.calibration, 10));
    },
    async addGroup(key) {
      await store.createGroup(key);
      this.groupListKey++;
    },
    async deleteGroup(key) {
      if (confirm(`Delete group "${this.groups[key].name}?"`)) {
        await store.removeGroup(key);
        this.groupListKey++;
      }
    },
    getOrderedGroups() {
      // Does not work in computed properties
      return _.fromPairs(_.sortBy(_.toPairs(this.groups), (g) => {
        return g[1].range_start;
      }));
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
          autocomplete="off"
          v-model="sacn"
          @change="updateSACN"
        >
          <option value="0">Off</option>
          <option value="1">On</option>
        </select>
      </span>
    </div>
    <div class="input-row input-row-top-margin input-toplevel">
      <span class="label select-label">Test Color Correction:</span>
      <span class="select-container">
        <select
          autocomplete="off"
          v-model="calibration"
          @change="updateCalibration"
        >
          <option value="0">Off</option>
          <option value="1">On</option>
        </select>
      </span>
    </div>
    <br />
    <div v-for="(group, k, i) in getOrderedGroups()" :key="k + groupListKey">
      <h4>Group {{ i + 1 }}</h4>
      <group-config
        v-bind:name="k"
      ></group-config>
      <div class="input-row input-row-top-margin">
        <a
          class="button"
          @click="addGroup(k)"
        >Add</a>
        <a
          class="button"
          v-show="k !== 'main'"
          @click="deleteGroup(k)"
        >Remove</a>
      </div>
    </div>
  `,
}

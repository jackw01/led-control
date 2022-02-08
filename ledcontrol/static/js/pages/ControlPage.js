// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  name: 'ControlPage',
  computed: {
    brightnessLimit: function() {
      console.log(store.get('global_brightness_limit'));
      return store.get('global_brightness_limit');
    },
    groups: function() {
      return store.get('groups');
    }
  },
  template: `
    <slider-number-input
      path="global_brightness"
      label="Brightness"
      unit=""
      v-bind:min="0"
      v-bind:max="brightnessLimit"
      v-bind:step="0.01"
    ></slider-number-input>
    <slider-number-input
      path="global_saturation"
      label="Saturation"
      unit=""
      v-bind:min="0"
      v-bind:max="1"
      v-bind:step="0.01"
    ></slider-number-input>
    <br />
    <group-controls
      v-for="(group, k, i) in groups"
      v-bind:name="k"
      v-bind:i="i"
    ></group-controls>
  `
}

// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

import store from '../Store.js';

export default {
  name: 'ControlPage',
  data() {
    return {
      presetKey: '',
      presetSavedKey: 0,
      presetLoaded: false,
    }
  },
  computed: {
    brightnessLimit: function() {
      return store.get('global_brightness_limit');
    },
    groups: function() {
      return store.get('groups');
    },
    orderedGroups: function() {
      return _.fromPairs(_.sortBy(_.toPairs(this.groups), (g) => {
        return g[1].range_start;
      }));
    },
    presets: function() {
      return store.getPresets();
    }
  },
  methods: {
    savePreset() {
      if (this.presetKey === '') alert('Please enter a name for this preset.')
      else {
        this.presetLoaded = true;
        store.savePreset(this.presetKey);
        this.presetSavedKey++;
      }
    },
    deletePreset() {
      if (confirm(`Delete preset "${this.presetKey}?"`)) {
        store.removePreset(this.presetKey);
        this.presetKey = '';
        this.presetLoaded = false;
      }
    },
    loadPreset() {
      this.presetLoaded = true;
      store.loadPreset(this.presetKey);
    }
  },
  template: `
    <slider-number-input
      path="global_brightness"
      label="Global Brightness"
      unit=""
      v-bind:min="0"
      v-bind:max="brightnessLimit"
      v-bind:step="0.01"
    ></slider-number-input>
    <slider-number-input
      path="global_saturation"
      label="Global Saturation"
      unit=""
      v-bind:min="0"
      v-bind:max="1"
      v-bind:step="0.01"
    ></slider-number-input>
    <div class="input-row input-row-top-margin input-toplevel">
      <span class="label select-label">Preset:</span>
      <span class="select-container">
        <select
          autocomplete="off"
          v-model="presetKey"
          @change="loadPreset"
        >
          <option
            v-for="(p, id) in presets"
            v-bind:value="id"
            :key="id + presetSavedKey"
          >
            {{ id }}
          </option>
        </select>
      </span>
    </div>
    <div class="input-row input-row-bottom-margin">
      <a
        class="button"
        @click="savePreset"
      >Save Preset</a>
      <a
        class="button"
        @click="deletePreset"
        v-show="presetLoaded"
      >Delete</a>
      <input
        type="text"
        v-model="presetKey"
        placeholder="preset name"
        autocomplete="off"
      >
    </div>
    <br />
    <div v-for="(group, k, i) in orderedGroups" :key="k">
      <h4>Group {{ i + 1 }} ({{ group.name }})</h4>
      <group-controls
        v-bind:name="k"
        :key="presetKey"
      ></group-controls>
      <br />
    </div>
  `
}

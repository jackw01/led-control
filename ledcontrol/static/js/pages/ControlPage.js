import store from '../Store.js';

export default {
  name: 'ControlPage',
  computed: {
    groups: function () {
      return store.get('groups');
    }
  },
  template: `
    <div>
      <slider-number-input
        path="global_brightness"
        label="Brightness"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
      <slider-number-input
        path="global_color_temp"
        label="Color Temp"
        unit="K"
        v-bind:min="1000"
        v-bind:max="12000"
        v-bind:step="10"
      ></slider-number-input>
      <slider-number-input
        path="global_saturation"
        label="Saturation"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
    </div>
    <br />
    <group-controls
      v-for="(group, k, i) in groups"
      v-bind:name="k"
      v-bind:i="i"
    ></group-controls>
  `
}

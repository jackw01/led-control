export default {
  name: 'ControlPage',
  created() {
    this.form = [
      {
        'key': 'b',
        'label': 'Brightness',
        'unit': '',
        'min': 0,
        'max': 1,
        'step': 0.01,
      }
    ];
  },
  template: `
    <div>
      <slider-number-input
        k="brightness"
        label="Brightness"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
      <slider-number-input
        k="color_temp"
        label="Color Temp"
        unit="K"
        v-bind:min="1000"
        v-bind:max="12000"
        v-bind:step="10"
      ></slider-number-input>
      <slider-number-input
        k="saturation"
        label="Saturation"
        unit=""
        v-bind:min="0"
        v-bind:max="1"
        v-bind:step="0.01"
      ></slider-number-input>
    </div>
  `
}

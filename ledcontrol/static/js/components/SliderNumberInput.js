export default {
  props: {
    'k': String,
    'label': String,
    'unit': String,
    'min': Number,
    'max': Number,
    'step': Number,
  },
  data() {
    return {
      val: 0
    }
  },
  methods: {
    update(event) {
      console.log(this);
      console.log(this.k);
      axios.post('/setparam', { key: this.k, value: this.val });
    }
  },
  template: `
    <div class="input-toplevel">
      <span class="label">{{ label }}:
        <span class="number-units" v-if="unit.length > 0">({{ unit }})</span>
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
          >
        </div>
      </div>
    </div>
  `,
};

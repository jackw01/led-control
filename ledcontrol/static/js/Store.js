// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

class Store {
  constructor() {
    this.settings = {};
    this.presets = {};
    this.functions = {};
    this.palettes = {};
  }

  async load() {
    let req = await axios.get('/getsettings');
    this.settings = req.data;
    console.log('Settings loaded:', this.settings);

    req = await axios.get('/getpresets');
    this.presets = req.data;
    console.log('Presets loaded:', this.presets);

    req = await axios.get('/getfunctions');
    this.functions = req.data;
    console.log('Functions loaded:', this.functions);

    req = await axios.get('/getpalettes');
    this.palettes = req.data;
    console.log('Palettes loaded:', this.palettes);
  }

  get(path) {
    return _.get(this.settings, path);
  }

  async set(path, value) {
    _.set(this.settings, path, value);
    console.log('Store set:', path, value);

    const delta = {};
    _.set(delta, path, value);
    await axios.post('/updatesettings', delta);
  }

  async setMultiple(pairs) {
    const delta = {};
    Object.entries(pairs).forEach(([path, value]) => {
      _.set(this.settings, path, value);
      console.log('Store set:', path, value);
      _.set(delta, path, value);
    });
    await axios.post('/updatesettings', delta);
  }

  async pushAllSettings() {
    await axios.post('/updatesettings', this.settings);
  }

  getPresets() {
    return this.presets;
  }

  async savePreset(key) {
    this.presets[key] = {};
    Object.entries(this.settings.groups).forEach(([k, v]) => {
      this.presets[key][k] = {
        brightness: v.brightness,
        color_temp: v.color_temp,
        saturation: v.saturation,
        function: v.function,
        palette: v.palette,
        scale: v.scale,
        speed: v.speed,
      };
    });
    console.log('Preset saved:', key);
    console.log(this.presets);
    await axios.post('/updatepreset', { key, value: this.presets[key] });
  }

  loadPreset(key) {
    console.log('Loading preset:', key);
    Object.entries(this.presets[key]).forEach(([k, v]) => {
      if (this.settings.groups.hasOwnProperty(k)) {
        let warn = false;
        if (!this.functions.hasOwnProperty(v.function)) {
          v.function = 0;
          warn = true;
        }
        if (!this.palettes.hasOwnProperty(v.palette)) {
          v.palette = 0;
          warn = true;
        }
        if (warn) alert('Preset contained a reference to an animation pattern or palette which has been deleted.')
        Object.assign(this.settings.groups[k], v);
      }
    });
    this.pushAllSettings();
  }

  async removePreset(key) {
    delete this.presets[key];
    console.log('Preset removed:', key);
    await axios.post('/removepreset', { key });
  }

  async createGroup(key) {
    const newGroup = _.cloneDeep(this.settings.groups[key]);
    newGroup.name = `untitled ${Object.keys(this.settings.groups).length}`;
    this.settings.groups[`g_${Date.now()}`] = newGroup;
    console.log('Group duplicated:', key);
    console.log(this.settings.groups);
    await this.pushAllSettings();
  }

  async removeGroup(key) {
    delete this.settings.groups[key];
    console.log('Group removed:', key);
    await axios.post('/removegroup', { key });
  }

  getFunctions() {
    return this.functions;
  }

  async requestCompile(key) {
    const req = await axios.post('/compilefunction', { key });
    return req.data;
  }

  async setFunction(key, value) {
    this.functions[key] = value;
    console.log('Function set:', key, value);
    await axios.post('/updatefunction', { key, value });
  }

  async removeFunction(key) {
    delete this.functions[key];
    console.log('Function removed:', key);
    await axios.post('/removefunction', { key });
  }

  getPalettes() {
    return this.palettes;
  }

  async setPalette(key, value) {
    this.palettes[key] = value;
    console.log('Palette set:', key, value);
    await axios.post('/updatepalette', { key, value });
  }

  async removePalette(key) {
    delete this.palettes[key];
    console.log('Palette removed:', key);
    await axios.post('/removepalette', { key });
  }
}

const instance = new Store();
export default instance;

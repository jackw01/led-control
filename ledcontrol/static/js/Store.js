// led-control WS2812B LED Controller Server
// Copyright 2022 jackw01. Released under the MIT License (see LICENSE for details).

class Store {
  constructor() {
    this.settings = {};
    this.functions = {};
    this.palettes = {};
  }

  async load() {
    let req = await axios.get('/getsettings');
    this.settings = req.data;
    console.log('Settings loaded:', this.settings);

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

  async pushAllSettings() {
    await axios.post('/updatesettings', this.settings);
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

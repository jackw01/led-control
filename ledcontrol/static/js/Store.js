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

  set(path, value) {
    _.set(this.settings, path, value);
    console.log('Store set:', path, value);
  }

  getFunctions() {
    return this.functions;
  }

  getPalettes() {
    return this.palettes;
  }

  setPalette(key, value) {
    this.palettes[key] = value;
    console.log('Palette set:', key, value);
  }

  removePalette(key) {
    delete this.palettes[key];
    console.log('Palette removed:', key);
  }

  saveSettings() {
    axios.post('/updatesettings', this.settings);
  }
}

const instance = new Store();
export default instance;

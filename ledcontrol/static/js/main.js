// led-control WS2812B LED Controller Server
// Copyright 2021 jackw01. Released under the MIT License (see LICENSE for details).

// Really should have used React or Vue for this but from my experience it would likely not build on a Raspberry Pi Zero due to the RAM limit
// Enjoy my jquery spaghetti code lol

defaultCodeComment = '# Code editing and renaming disabled on default patterns. Click "New Pattern" to create and edit a copy of this pattern.\n\n';

function handleInputChange(elem) {
  const key = elem.data('id');
  let val = elem.val();
  if (!elem.is('input[type=text]')) val = parseFloat(val, 10);
  // Sliders or numbers - enforce min/max and update other input
  if (!elem.is('select') && !elem.is('input[type=text]')) {
    const min = parseFloat(elem.attr('min'), 10);
    const max = parseFloat(elem.attr('max'), 10);
    if (val < min) val = min;
    if (val > max) val = max;
    if (elem.attr('type') == 'range') $('input[type=number][data-id=' + key + ']').val(val);
    else $('input[type=range][data-id=' + key + ']').val(val);
  }

  // On primary pattern change, update code and speed/scale
  if (key === 'primary_pattern') {
    $.getJSON('/getpatternparams', { key: val }, (result) => {
      $('input[data-id=primary_speed]').val(result.speed);
      $('input[data-id=primary_scale]').val(result.scale);
      updateCodeView(val);
    });
  }

  // On palette change, update color pickers
  if (key === 'palette') updateColorPickers(val);

  // On sACN mode change, hide or show UI
  if (key === 'sacn') {
    const elems = $('.input-toplevel:not(.input-toplevel[data-id=brightness], .input-toplevel[data-id=color_temp], .input-toplevel[data-id=sacn]), #code, #palette-color-bar, #colors');
    if (val === 1) elems.hide();
    else elems.show();
  }

  return { key: key, value: val };
}

// When a slider is moved, update number input without setting params
function handleParamAdjust() {
  handleInputChange($(this));
}

// When a slider is dropped or a number input is changed, set params
function handleParamUpdate() {
  $.getJSON('/setparam', handleInputChange($(this)), () => {});
}

// Create copy of current pattern
function handleNewPattern() {
  // Clear compile status
  statusClass = 'none';
  status = 'Pattern not compiled yet';
  updateSourceStatus();

  // Set new source and name, add option
  const key = getCurrentPatternKey();
  const newKey = Date.now();
  sources[newKey] = codeMirror.getValue().replace(defaultCodeComment, '');
  names[newKey] = names[key] + ' (Copy)';
  $('select[data-id="primary_pattern"]')
    .append(`<option value="${newKey}">${names[newKey]}</option>`)
    .val(newKey);

  // Update code and button states, send everything to the server
  updateCodeView(newKey);
  handleCompile(() => { // Compile first
    $.getJSON('/setpatternname', { key: newKey, name: names[newKey] }, () => {}); // Set name
    $.getJSON('/setparam', { key: 'primary_pattern', value: newKey }, () => {}); // Select
  });
}

// Delete current pattern
function handleDeletePattern() {
  if (confirm(`Delete pattern "${$('#pattern-name').val()}?"`)) {
    const key = getCurrentPatternKey();
    $('select[data-id="primary_pattern"]').val(0);
    $(`select[data-id="primary_pattern"] option[value="${key}"]`).remove();
    handleInputChange($('select[data-id="primary_pattern"]'));
    $.getJSON('/setparam', { key: 'primary_pattern', value: 0 }, () => {
      $.getJSON('/deletepattern', { key: key }, () => {});
    });
  }
}

// Rename current pattern
function handleRenamePattern() {
  const key = getCurrentPatternKey();
  const newName = $('#pattern-name').val();
  names[key] = newName;
  $('select[data-id="primary_pattern"] option[value=' + key + ']').html(newName);
  $.getJSON('/setpatternname', { key: key, name: newName }, () => {});
}

// Compile selected pattern
function handleCompile(callback) {
  const key = getCurrentPatternKey();
  const source = codeMirror.getValue();
  sources[key] = source;
  $.getJSON('/compilepattern', {
    key: key,
    source: source,
  }, (result) => {
      console.log('Compile errors/warnings:', result.errors, result.warnings);
      if (result.errors.length === 0) { // && result.warnings.length === 0) {
        statusClass = 'success';
        status = 'Pattern compiled successfully';
      } else if (result.errors.length === 0 && result.warnings.length > 0) {
        //statusClass = 'warning';
        //status = 'Pattern generated warnings: ' + result.warnings.join(', ');
      } else if (result.errors.length > 0) {
        statusClass = 'error';
        status = result.errors.join(', ');
      }
      updateSourceStatus();
      if (callback) callback();
  });
}

// Update color classes on source status element
function updateSourceStatus() {
  $('#source-status').text(status);
  statusClasses.forEach((c) => {
    if (statusClass === c) $('#source-status').addClass('status-' + c);
    else $('#source-status').removeClass('status-' + c);
  });
}

// Update code viewer, buttons, and pattern name with new pattern key
function updateCodeView(newKey) {
  $('#pattern-name').val(names[newKey]);
  let code = sources[newKey].trim();
  if (defaultSourceKeys.indexOf(newKey) >= 0) { // Prevent editing default patterns
    code = defaultCodeComment + code;
    codeMirror.setOption('readOnly', true);
    $('#pattern-name').prop('disabled', true);
    $('#delete-pattern').hide();
  } else {
    codeMirror.setOption('readOnly', false);
    $('#pattern-name').prop('disabled', false);
    $('#delete-pattern').show();
  }
  codeMirror.setValue(code);
}

// Send the current palette to the server
function updateCurrentPalette() {
  updatePaletteColorBar();
  const key = getCurrentPaletteKey();
  $.getJSON('/setpalette', {
    key: key, value: JSON.stringify(palettes[key])
  }, () => { });
}

// Create copy of current palette
function handleNewPalette() {
  // Set new source and name, add option
  const key = getCurrentPaletteKey();
  const newKey = Date.now();
  palettes[newKey] = JSON.parse(JSON.stringify(palettes[key])); // This a hack but it works
  palettes[newKey].name = palettes[key].name + ' (Copy)';
  $('select[data-id="palette"]')
    .append(`<option value="${newKey}">${palettes[newKey].name}</option>`)
    .val(newKey);
  updateColorPickers(newKey);
  updateCurrentPalette();
  $.getJSON('/setparam', { key: 'palette', value: newKey }, () => { });
}

// Delete current palette
function handleDeletePalette() {
  if (confirm(`Delete palette "${$('#palette-name').val()}?"`)) {
    const key = getCurrentPaletteKey();
    delete palettes[key];
    $('select[data-id="palette"]').val(0);
    $(`select[data-id="palette"] option[value="${key}"]`).remove();
    handleInputChange($('select[data-id="palette"]'));
    $.getJSON('/setparam', { key: 'palette', value: 0 }, () => {
      $.getJSON('/deletepalette', { key: key }, () => { });
    });
  }
}

// Rename current palette
function handleRenamePalette() {
  const key = getCurrentPaletteKey();
  const newName = $('#palette-name').val();
  palettes[key].name = newName;
  $('select[data-id="palette"] option[value=' + key + ']').html(newName);
  updateCurrentPalette();
}

// Update palette preview
function updatePaletteColorBar() {
  const palette = palettes[getCurrentPaletteKey()];
  const c = document.getElementById('palette-color-bar');
  const ctx = c.getContext('2d');
  c.width = 64;
  c.height = 1;
  const sectorSize = 1 / (palette.colors.length - 1);
  for (let i = 0; i < c.width; i++) {
    let f = i / c.width;
    const sector = Math.floor(f / sectorSize);
    f = f % sectorSize / sectorSize;
    const c1 = palette.colors[sector];
    const c2 = palette.colors[sector + 1];
    let h1 = c2[0] - c1[0];
    // Allow full spectrum if extremes are 0 and 1 in any order
    // otherwise pick shortest path between colors
    if (Math.abs(h1) != 1) {
      if (h1 < -0.5) h1++;
      if (h1 > 0.5) h1--;
    }
    const h = (f * h1 + c1[0]) * 360;
    const s = (f * (c2[1] - c1[1]) + c1[1]) * 100;
    const v = (f * (c2[2] - c1[2]) + c1[2]) * 100;
    const l = (2 - s / 100) * v / 2;
    const s2 = s * v / (l < 50 ? l * 2 : 200 - l * 2);
    ctx.fillStyle = `hsl(${h}, ${s}%, ${l}%)`
    ctx.fillRect(i, 0, 1, c.height);
  }
  /*
  Object.values(palettes).forEach((palette) => {
    const nc = document.createElement('canvas');
    nc.style.display = 'block';
    nc.style.borderRadius = '3px';
    nc.style.width = '100%';
    nc.style.height = '1.7rem';
    nc.style.marginBottom = '1.5rem';
    document.getElementById('main').insertBefore(nc, c);
    const ctx = nc.getContext('2d');
    nc.width = 64;
    nc.height = 1;
    const sectorSize = 1 / (palette.colors.length - 1);
    for (let i = 0; i < nc.width; i++) {
      let f = i / nc.width;
      const sector = Math.floor(f / sectorSize);
      f = f % sectorSize / sectorSize;
      const c1 = palette.colors[sector];
      const c2 = palette.colors[sector + 1];
      const h1 = c2[0] - c1[0];
      const h2 = c2[0] - 1 - c1[0];
      const h = (f * (Math.abs(h1) < Math.abs(h2) || h1 === 1 ? h1 : h2) + c1[0]) * 360;
      const s = (f * (c2[1] - c1[1]) + c1[1]) * 100;
      const v = (f * (c2[2] - c1[2]) + c1[2]) * 100;
      const l = (2 - s / 100) * v / 2;
      const s2 = s * v / (l < 50 ? l * 2 : 200 - l * 2);
      ctx.fillStyle = `hsl(${h}, ${s}%, ${l}%)`
      ctx.fillRect(i, 0, 1, nc.height);
    }
  });*/
}

// Update color pickers for selected palette
function updateColorPickers(newKey) {
  const palette = palettes[newKey];
  $('#palette-name').val(palette.name);
  const disabled = defaultPaletteKeys.indexOf(newKey) >= 0;
  if (disabled) { // Prevent editing default palettes
    $('#palette-name').prop('disabled', true);
    $('#delete-palette').hide();
    $('#color-picker-container').css('pointer-events', 'none');
  } else {
    $('#palette-name').prop('disabled', false);
    $('#delete-palette').show();
    $('#color-picker-container').css('pointer-events', 'auto');
  }

  const container = $('#color-picker-container');
  container.empty();

  for (let i = 0; i < palette.colors.length; i++) {
    container.append(`<div class="input-row input-row-top-margin"><span class="label"> Color ${i + 1}:</span><a class="button button-inline palette-color-control" id="add-color-${i}">+</a><a class="button button-inline palette-color-control" id="delete-color-${i}">-</a></div><span class="color-picker" id="color-picker-${i}"></span>`);
    const pickr = Pickr.create({
      el: `#color-picker-${i}`,
      theme: 'classic',
      showAlways: true,
      inline: true,
      lockOpacity: true,
      comparison: false,
      default: `hsv(${palette.colors[i][0] * 360}, ${palette.colors[i][1] * 100}%, ${palette.colors[i][2] * 100}%)`,
      swatches: null,
      components: {
        preview: false,
        opacity: false,
        hue: true,
        interaction: { hex: true, rgba: true, hsla: true, hsva: true, input: true },
      },
    });
    pickr.index = i;

    if (!disabled) {
      pickr.on('changestop', (instance) => {
        const color = instance.getColor();
        palettes[getCurrentPaletteKey()].colors[instance.index] = [
          color.h / 360, color.s / 100, color.v / 100
        ];
        updateCurrentPalette();
      });

      $(`#add-color-${i}`).on('click', () => {
        const key = getCurrentPaletteKey();
        palettes[key].colors.splice(i + 1, 0, palettes[key].colors[i].slice());
        updateColorPickers(key);
        updateCurrentPalette();
      });

      $(`#delete-color-${i}`).on('click', () => {
        const key = getCurrentPaletteKey();
        if (palettes[key].colors.length > 2) {
          palettes[key].colors.splice(i, 1);
          updateColorPickers(key);
          updateCurrentPalette();
        }
      });
    } else {
      $('.palette-color-control').hide();
    }
  }

  updatePaletteColorBar();
}

function getCurrentPatternKey() {
  return parseInt($('select[data-id="primary_pattern"]').val(), 10);
}

function getCurrentPaletteKey() {
  return parseInt($('select[data-id="palette"]').val(), 10);
}

let codeMirror, sources, names, defaultSourceKeys, palettes, defaultPaletteKeys;
const statusClasses = ['none', 'success', 'warning', 'error'];
let statusClass = 'none';
let status = 'Pattern not compiled yet';

window.onload = function() {
  $('input[type=range].update-on-change').on('mousemove touchmove', handleParamAdjust);
  $('.update-on-change').on('change', handleParamUpdate);
  $('#new-pattern').on('click', handleNewPattern);
  $('#delete-pattern').on('click', handleDeletePattern);
  $('#pattern-name').on('change', handleRenamePattern);
  $('#compile').on('click', handleCompile);
  $('#new-palette').on('click', handleNewPalette);
  $('#delete-palette').on('click', handleDeletePalette);
  $('#palette-name').on('change', handleRenamePalette);

  handleInputChange($('select[data-id="sacn"]'));

  $.getJSON('/getpatternsources', {}, (result) => {
    console.log('Sources:', result);
    // Set selected pattern to correct value
    sources = result.sources;
    names = result.names;
    defaultSourceKeys = result.defaults;
    Object.entries(names).forEach(([k, v]) => {
      $('select[data-id="primary_pattern"]').append(`<option value="${k}">${v}</option>`);
    });
    $('select[data-id="primary_pattern"]').val(result.current);

    // Update compile status display
    updateSourceStatus();

    // Display code for starting pattern
    codeMirror = CodeMirror(document.getElementById('code'), {
      value: '',
      mode: 'python',
      indentUnit: 4,
      lineNumbers: true,
      lineWrapping: true,
      theme: 'summer-night',
    });
    codeMirror.setOption('extraKeys', {
      Tab: function(cm) {
        const spaces = Array(cm.getOption('indentUnit') + 1).join(' ');
        cm.replaceSelection(spaces);
      }
    });
    updateCodeView(result.current);
  });

  $.getJSON('/getpalettes', {}, (result) => {
    console.log('Palettes:', result);
    // Set selected palette to current value
    palettes = result.palettes;
    defaultPaletteKeys = result.defaults;
    Object.entries(palettes).forEach(([k, v]) => {
      $('select[data-id="palette"]').append(`<option value="${k}">${v.name}</option>`);
    });
    $('select[data-id="palette"]').val(result.current);

    // Generate color pickers
    updateColorPickers(result.current);
  });
};

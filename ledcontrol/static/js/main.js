// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

defaultCodeComment = '# Code editing and renaming disabled on default patterns. Click "New Pattern" to create and edit a copy of this pattern.\n\n';

function handleInputChange(elem) {
  const key = elem.data('id');
  let val = parseFloat(elem.val(), 10);
  if (!elem.is('select')) { // Sliders or numbers - enforce min/max and update other input
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
    $.getJSON('/setpatternname', { key: newKey, name: names[newKey] }, () => { }); // Set name
    $.getJSON('/setparam', { key: 'primary_pattern', value: newKey }, () => { }); // Select
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
      $.getJSON('/deletepattern', { key: key }, () => { });
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
  $.getJSON('/compilepattern', {
    key: getCurrentPatternKey(),
    source: codeMirror.getValue(),
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

// Update color pickers for selected palette
function updateColorPickers() {
  const palette = palettes[getCurrentPaletteKey()];
  const container = $('#color-picker-container');
  container.empty();

  for (let i = 0; i < palette.colors.length; i++) {
    container.append(`<div class="input-row input-row-top-margin"><span class="label"> Color ${i}:</span></div><span class="color-picker" id="color-picker-${i}"></span>`);

    const pickr = Pickr.create({
      el: `#color-picker-${i}`,
      theme: 'classic',
      showAlways: true,
      inline: true,
      lockOpacity: true,
      comparison: true,
      default: `hsv(${palette.colors[i][0] * 360}, ${palette.colors[i][1] * 100}%, ${palette.colors[i][2] * 100}%)`,
      swatches: null,
      components: {
        preview: true,
        opacity: false,
        hue: true,
        interaction: { hex: true, rgba: true, hsla: true, hsva: true, input: true },
      },
    });
    pickr.index = i;
    pickr.on('changestop', (instance) => {
      const color = instance.getColor();

    })
  }
}

function getCurrentPatternKey() {
  return parseInt($('select[data-id="primary_pattern"]').val(), 10);
}

function getCurrentPaletteKey() {
  return parseInt($('select[data-id="palette"]').val(), 10);
}

let codeMirror, sources, names, defaultSourceKeys, palettes;
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
    updateCodeView(result.current);
  });

  $.getJSON('/getpalettes', {}, (result) => {
    console.log('Palettes:', result);
    // Set selected palette to current value
    palettes = result.palettes;
    Object.entries(palettes).forEach(([k, v]) => {
      $('select[data-id="palette"]').append(`<option value="${k}">${v.name}</option>`);
    });
    $('select[data-id="palette"]').val($('select[data-id="palette"]').data('value'));

    // Generate color pickers
    updateColorPickers();
  });
};

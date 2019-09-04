// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

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
    return { key: key, value: val };
  }
  if (key === 'primary_pattern') { // On primary pattern change, update code display
    updateCodeView(val);
    return { key: key, value: val };
  }
}

// When a slider is moved, update number input without setting params
function handleParamAdjust() {
  handleInputChange($(this));
}

// When a slider is dropped or a number input is changed, set params
function handleParamUpdate() {
  $.getJSON('/setparam', handleInputChange($(this)), () => {});
}

function handleColorUpdate() {
  const elem = $(this);
  const idx = elem.data('idx');
  const cmp = elem.data('cmp');
  const val = parseFloat(elem.val(), 10);
  const min = parseFloat(elem.attr('min'), 10);
  const max = parseFloat(elem.attr('max'), 10);
  if (val < min || val > max) return;
  $.getJSON('/setcolor', { index: idx, component: cmp, value: val, }, () => {});
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
  sources[newKey] = sources[key];
  names[newKey] = names[key] + ' (Copy)';
  $('select[data-id="primary_pattern"]')
    .append(`<option value="${newKey}">${names[newKey]}</option>`)
    .val(newKey);

  // Update code and button states, send everything to the server
  updateCodeView(newKey);
  handleCompile(); // Compile first
  $.getJSON('/setpatternname', { key: newKey, name: names[newKey] }, () => {}); // Set name
  $.getJSON('/setparam', { key: 'primary_pattern', value: newKey }, () => {}); // Select
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
function handleCompile() {
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
    code = '# Code editing and renaming disabled on default patterns. Click "New Pattern" to create and edit a copy of this pattern.\n\n' + code;
    codeMirror.setOption('readOnly', true);
    $('#pattern-name').prop('disabled', true);
  } else {
    codeMirror.setOption('readOnly', false);
    $('#pattern-name').prop('disabled', false);
  }
  codeMirror.setValue(code);
}

function getCurrentPatternKey() {
  return parseInt($('select[data-id="primary_pattern"]').val(), 10);
}

let codeMirror, sources, names, defaultSourceKeys;
const statusClasses = ['none', 'success', 'warning', 'error'];
let statusClass = 'none';
let status = 'Pattern not compiled yet';

window.onload = function() {
  $('input[type=range].update-on-change').on('mousemove touchmove', handleParamAdjust);
  $('.update-on-change').on('change', handleParamUpdate);
  $('.update-color-on-change').on('change mousemove touchmove', handleColorUpdate);
  $('#new-pattern').on('click', handleNewPattern);
  $('#pattern-name').on('change', handleRenamePattern);
  $('#compile').on('click', handleCompile);

  $.getJSON('/getpatternsources', {}, (result) => {
    console.log('Sources:', result);
    // Set selected pattern to correct value
    sources = result.sources;
    names = result.names;
    defaultSourceKeys = result.defaults;
    Object.entries(names).forEach(([k, v]) => {
      if (!defaultSourceKeys.includes(k)) {
        $('select[data-id="primary_pattern"]').append(`<option value="${k}">${v}</option>`);
      }
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
};

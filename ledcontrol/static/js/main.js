// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

function handleInputChange(elem) {
  var key = elem.data('id');
  var val = parseFloat(elem.val(), 10);
  if (!elem.is('select')) { // Sliders or numbers - enforce min/max and update other input
    var min = parseFloat(elem.attr('min'), 10);
    var max = parseFloat(elem.attr('max'), 10);
    if (val < min) val = min;
    if (val > max) val = max;
    if (elem.attr('type') == 'range') $('input[type=number][data-id=' + key + ']').val(val);
    else $('input[type=range][data-id=' + key + ']').val(val);
    return { key: key, value: val };
  }
  if (key === 'primary_pattern') { // On primary pattern change, update code display
    var newPatternSourceKey = Object.keys(sources)[val];
    updateCodeView(newPatternSourceKey);
    return { key: key, value: newPatternSourceKey };
  }
}

// When a slider is moved, update number input without setting params
function handleParamAdjust() {
  handleInputChange($(this));
}

// When a slider is dropped or a number input is changed, set params
function handleParamUpdate() {
  var newVal = handleInputChange($(this));
  $.getJSON('/setparam', newVal, function() {});
}

function handleColorUpdate() {
  var elem = $(this);
  var idx = elem.data('idx');
  var cmp = elem.data('cmp');
  var val = parseFloat(elem.val(), 10);
  var min = parseFloat(elem.attr('min'), 10);
  var max = parseFloat(elem.attr('max'), 10);
  if (val < min || val > max) return;
  $.getJSON('/setcolor', { index: idx, component: cmp, value: val, }, function() {});
}

function handleNewPattern() {

}

// Compile selected pattern
function handleCompile() {
  $.getJSON('/compilepattern', {
    key: getCurrentPatternKey(),
    source: codeMirror.getValue(),
  }, function(result) {
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
  statusClasses.forEach(function (c) {
    if (statusClass === c) $('#source-status').addClass('status-' + c);
    else $('#source-status').removeClass('status-' + c);
  });
}

// Update code viewer with new pattern key
function updateCodeView(newKey) {
  var code = sources[newKey].trim();
  if (defaultSourceKeys.indexOf(newKey) >= 0) { // Prevent editing default patterns
    code = '# Code editing disabled on default patterns. Click "New Pattern" to create and edit a copy of this pattern.\n\n' + code;
    codeMirror.setOption('readOnly', true);
  } else {
    codeMirror.setOption('readOnly', false);
  }
  codeMirror.setValue(code);
}

function getCurrentPatternKey() {
  var currentIndex = parseInt($('select[data-id="primary_pattern"]').val(), 10);
  return Object.keys(sources)[currentIndex];
}

var codeMirror, sources, defaultSourceKeys;
var statusClasses = ['none', 'success', 'warning', 'error'];
var statusClass = 'none';
var status = 'Pattern not compiled yet';

window.onload = function() {
  $('input[type=range].update-on-change').on('mousemove touchmove', handleParamAdjust);
  $('.update-on-change').on('change', handleParamUpdate);
  $('.update-color-on-change').on('change mousemove touchmove', handleColorUpdate);
  $('#new-pattern').on('click', handleNewPattern);
  $('#compile').on('click', handleCompile);

  $.getJSON('/getpatternsources', {}, function (result) {
    console.log('Sources:', result.sources);
    // Set selected pattern to correct value
    sources = result.sources;
    defaultSourceKeys = result.defaults;
    $('select[data-id="primary_pattern"]').val(Object.keys(sources).indexOf(result.current));

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

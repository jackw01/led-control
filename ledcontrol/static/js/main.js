// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

function handleParamUpdate() {
  var elem = $(this);
  var key = elem.data('id');
  var val = parseFloat(elem.val(), 10);
  if (!elem.is('select')) {
    var min = parseFloat(elem.attr('min'), 10);
    var max = parseFloat(elem.attr('max'), 10);
    var power = parseFloat(elem.data('power'), 10);
    if (val < min || val > max) return;
    if (elem.attr('type') == 'range') {
      val = Math.min(Math.max(Math.pow(val / max, power) * max, min), max);
      $('input[type=number][data-id=' + key + ']').val(val);
    } else {
      $('input[type=range][data-id=' + key + ']').val(Math.pow(val / max, 1.0 / power) * max);
    }
  }
  //$('*[data-id=' + key + ']').val(val);
  $.getJSON('/setparam', { key: key, value: val, }, function() {});
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

var codeMirror;

$('.update-on-change').on('change', handleParamUpdate);
$('.update-color-on-change').on('change mousemove touchmove', handleColorUpdate);

window.onload = function() {
  codeMirror = CodeMirror(document.getElementById('main'), {
    value: 'def pattern(t, dt, x, y, prev_state):\n    return(t + x, 0, prev_state[0])',
    mode: 'python',
    indentUnit: 4,
    lineNumbers: true,
    theme: 'summer-night',
  });
};

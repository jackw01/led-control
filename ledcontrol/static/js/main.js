// led-control WS2812B LED Controller Server
// Copyright 2019 jackw01. Released under the MIT License (see LICENSE for details).

function handleParamUpdate() {
  var elem = $(this);
  var key = elem.data('id');
  var val = parseFloat(elem.val(), 10);
  if (!elem.is('select')) {
    var min = parseFloat(elem.attr('min'), 10);
    var max = parseFloat(elem.attr('max'), 10);
    if (val < min || val > max) return;
  }
  $('*[data-id=' + key + ']').val(val);
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

$('.update-on-change').on('change', handleParamUpdate);
$('.update-color-on-change').on('change mousemove touchmove', handleColorUpdate);

window.onload = updateControls;

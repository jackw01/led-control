// led-control WS2812B LED Controller Server
// Copyright 2018 jackw01. Released under the MIT License (see LICENSE for details).

function updateControls() {
  if ($('*[data-id=color_animation_mode]').val() == 1) $('tr.saturation').show();
  else $('tr.saturation').hide();
  if ($('*[data-id=color_animation_mode]').val() == 2) $('tr.sine').show();
  else $('tr.sine').hide();
  if ($('*[data-id=secondary_animation_mode]').val() == 0) $('tr.a2').hide();
  else $('tr.a2').show();
}

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
  $.getJSON('/setparam', { key: key, value: val, }, function(data, status, jqXHR) {});
}

function handleColorUpdate() {
  var elem = $(this);
  var idx = elem.data('idx');
  var cmp = elem.data('cmp');
  var val = parseFloat(elem.val(), 10);
  var min = parseFloat(elem.attr('min'), 10);
  var max = parseFloat(elem.attr('max'), 10);
  if (val < min || val > max) return;
  $.getJSON('/setcolor', { index: idx, component: cmp, value: val, }, function(data, status, jqXHR) {});
}

$('.update-on-change').on('change', handleParamUpdate);
$('.update-color-on-change').on('change mousemove touchmove', handleColorUpdate);
$('*[data-id=color_animation_mode], *[data-id=secondary_animation_mode]').change(updateControls);

window.onload = updateControls;

// led-control WS2812B LED Controller Server
// Copyright 2018 jackw01. Released under the MIT License (see LICENSE for details).

function updateControls() {
  if ($('#color_animation_mode').val() == 1) $('tr.saturation').show();
  else $('tr.saturation').hide();
  if ($('#color_animation_mode').val() == 2) $('tr.sine').show();
  else $('tr.sine').hide();
  if ($('#secondary_animation_mode').val() == 0) $('tr.a2').hide();
  else $('tr.a2').show();
}

$('.update-on-change').on('change', function update(evt) {
  var key = $(this).data('id');
  var val = parseFloat($(this).val(), 10);
  if (!$(this).is('select')) {
    var min = parseFloat($(this).attr('min'), 10);
    var max = parseFloat($(this).attr('max'), 10);
    if (val < min || val > max) return;
  }
  $('*[data-id=' + key + ']').val(val);
  $.getJSON('/setparam', { key: key, value: val, }, function(data, status, jqXHR) {});
});

$('.update-color-on-change').on('change', function update(evt) {
  var idx = $(this).data('idx');
  var cmp = $(this).data('cmp');
  var val = parseFloat($(this).val(), 10);
  var min = parseFloat($(this).attr('min'), 10);
  var max = parseFloat($(this).attr('max'), 10);
  if (val < min || val > max) return;
  $.getJSON('/setcolor', { index: idx, component: cmp, value: val, }, function(data, status, jqXHR) {});
});

$('#color_animation_mode, #secondary_animation_mode').change(function update(evt) {
  updateControls();
});

window.onload = updateControls();

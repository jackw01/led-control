function updateControls() {
  if ($('#color_animation_mode').val() == 1) $('tr.saturation').show();
  else $('tr.saturation').hide();
  if ($('#color_animation_mode').val() == 2) $('tr.sine').show();
  else $('tr.sine').hide();
  if ($('#secondary_animation_mode').val() == 0) $('tr.a2').hide();
  else $('tr.a2').show();
}

$('.update-on-change').on('change', function update(evt) {
  var key = $(this).attr('id');
  var val = parseFloat($(this).val(), 10);
  $.getJSON('/setparam', { key: key, value: val, }, function(data, status, jqXHR) {});
});

$('#color_animation_mode, #secondary_animation_mode').change(function update(evt) {
  updateControls();
});

window.onload = updateControls();

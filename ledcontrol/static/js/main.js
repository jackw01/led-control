$('.update-on-change').change(function update(evt) {
  var key = $(this).attr('id');
  var val = parseFloat($(this).val(), 10);
  $.getJSON("/setparam", { key: key, value: val, }, function(data, status, jqXHR) {});
});

// SWIG interface file to define rpi_ws281x library python wrapper.
// Original author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
// Modified by jackw01 (github.com/jackw01) - 2019

// Define module name rpi_ws281x.  This will actually be imported under
// the name _rpi_ws281x following the SWIG & Python conventions.
%module rpi_ws281x

// Include standard SWIG types & array support for support of uint32_t
// parameters and arrays.
%include "stdint.i"
%include "carrays.i"

/*
%typemap(in) uint8_t value[ANY] (uint8_t temp[$1_dim0]) {
  int i;
  if (!PySequence_Check($input)) {
    PyErr_SetString(PyExc_ValueError,"Expected a sequence");
    return NULL;
  }
  if (PySequence_Length($input) != $1_dim0) {
    PyErr_SetString(PyExc_ValueError,"Size mismatch. Expected $1_dim0 elements");
    return NULL;
  }
  for (i = 0; i < $1_dim0; i++) {
    PyObject *o = PySequence_GetItem($input,i);
    if (PyInt_Check(o)) {
      temp[i] = (uint8_t)PyInt_AsLong(o);
    } else {
      PyErr_SetString(PyExc_ValueError,"Sequence elements must be numbers");
      return NULL;
    }
  }
  $1 = temp;
}*/
/*
%typemap(in) uint32_t values[ANY] (uint32_t temp[$1_dim0]) {
  int i;
  if (!PySequence_Check($input)) {
    PyErr_SetString(PyExc_ValueError,"Expected a sequence");
    return NULL;
  }
  if (PySequence_Length($input) != $1_dim0) {
    PyErr_SetString(PyExc_ValueError,"Size mismatch. Expected $1_dim0 elements");
    return NULL;
  }
  for (i = 0; i < $1_dim0; i++) {
    PyObject *o = PySequence_GetItem($input,i);
    if (PyInt_Check(o)) {
      temp[i] = (uint32_t)PyInt_AsLong(o);
    } else {
      PyErr_SetString(PyExc_ValueError,"Sequence elements must be numbers");
      return NULL;
    }
  }
  $1 = temp;
}
*/

%{
static int convert_color_array(PyObject *input, color_hsv *ptr, int size) {
  int i;
  if (!PySequence_Check(input)) {
    PyErr_SetString(PyExc_TypeError, "Expecting a sequence");
    return 0;
  }
  for (i =0; i < size; i++) {
    PyObject *o = PySequence_GetItem(input,i);
    if (!PyInt_Check(o)) {
     Py_XDECREF(o);
     PyErr_SetString(PyExc_ValueError, "Expecting a sequence of floats");
     return 0;
    }
    ptr[i] = PyInt_AsLong(o);
    Py_DECREF(o);
  }
  return 1;
}
%}

%typemap(in) color_hsv values[ANY] {
  int len = PyObject_Length($input);
  $1 = malloc(sizeof(uint32_t) * len);
  if (!convert_color_array($input, $1, len))
  {
    return NULL;
  }
}

%{
static int convert_iarray_32(PyObject *input, uint32_t *ptr, int size) {
  int i;
  if (!PySequence_Check(input)) {
    PyErr_SetString(PyExc_TypeError, "Expecting a sequence");
    return 0;
  }
  for (i =0; i < size; i++) {
    PyObject *o = PySequence_GetItem(input,i);
    if (!PyInt_Check(o)) {
     Py_XDECREF(o);
     PyErr_SetString(PyExc_ValueError, "Expecting a sequence of floats");
     return 0;
    }
    ptr[i] = PyInt_AsLong(o);
    Py_DECREF(o);
  }
  return 1;
}
%}

%typemap(in) uint32_t values[ANY] {
  int len = PyObject_Length($input);
  $1 = malloc(sizeof(uint32_t) * len);
  if (!convert_iarray_32($input, $1, len))
  {
    return NULL;
  }
}

%{
static int convert_iarray_8(PyObject *input, uint8_t *ptr, int size) {
  int i;
  if (!PySequence_Check(input)) {
    PyErr_SetString(PyExc_TypeError, "Expecting a sequence");
    return 0;
  }
  if (PyObject_Length(input) != size) {
    PyErr_SetString(PyExc_ValueError, "Sequence size mismatch");
    return 0;
  }
  for (i =0; i < size; i++) {
    PyObject *o = PySequence_GetItem(input,i);
    if (!PyInt_Check(o)) {
     Py_XDECREF(o);
     PyErr_SetString(PyExc_ValueError, "Expecting a sequence of floats");
     return 0;
    }
    ptr[i] = PyInt_AsLong(o);
    Py_DECREF(o);
  }
  return 1;
}
%}

%typemap(in) uint8_t * {
   $1 = malloc(sizeof(uint8_t) * 256);
   if (!convert_iarray_8($input,$1,256)) {
    return NULL;
   }
}


%typemap(out) uint8_t * {
  $result = PyList_New(256);
  int x;
  for(x = 0; x < 256; x++){
  PyList_SetItem($result, x, PyInt_FromLong($1[x]));
  }
}

// Declare functions which will be exported as anything in the ws2811.h header.
%{
#include "c/rpi_ws281x/ws2811.h"
#include "led_render.h"
%}

// Process ws2811.h header and export all included functions.
%include "c/rpi_ws281x/ws2811.h"

// Include render utils
%include "led_render.h"

/*
%inline %{
  uint32_t ws2811_led_get(ws2811_channel_t *channel, int lednum) {
    if (lednum >= channel->count) return -1;

    return channel->leds[lednum];
  }

  int ws2811_led_set(ws2811_channel_t *channel, int lednum, uint32_t color) {
    if (lednum >= channel->count) return -1;
    channel->leds[lednum] = color;

    return 0;
  }

  ws2811_channel_t *ws2811_channel_get(ws2811_t *ws, int channelnum) {
    return &ws->channel[channelnum];
  }
%}
*/

// SWIG interface file to define rpi_ws281x library python wrapper.
// Original author: Tony DiCola (tony@tonydicola.com), Jeremy Garff (jer@jers.net)
// Modified by jackw01 (github.com/jackw01) - 2019

// Define module name rpi_ws281x. This will actually be imported under
// the name _rpi_ws281x following the SWIG & Python conventions.
%module ledcontrol_rpi_ws281x_driver

// Include standard SWIG types & array support for support of uint32_tparameters and arrays.
%include "stdint.i"
%include "carrays.i"

// Unsafe, but ok in this case since inputs are hopefully consistent
%typemap(in) color_hsv values[ANY] {
  int len = PyObject_Length($input);
  $1 = malloc(sizeof(color_hsv) * len);
  int i, j;
  for (i = 0; i < len; i++) {
    PyObject *o = PySequence_GetItem($input, i);
    for (j = 0; j < 3; j++) {
      PyObject *o2 = PySequence_GetItem(o, j);
      $1[i].raw[j] = PyInt_AsLong(o2);
      Py_DECREF(o2);
    }
    Py_DECREF(o);
  }
}

%typemap(freearg) color_hsv values[ANY] {
   if ($1) free($1);
}

%typemap(in) color_hsv_float values[ANY] {
  int len = PyObject_Length($input);
  $1 = malloc(sizeof(color_hsv_float) * len);
  int i, j;
  for (i = 0; i < len; i++) {
    PyObject *o = PySequence_GetItem($input, i);
    for (j = 0; j < 3; j++) {
      PyObject *o2 = PySequence_GetItem(o, j);
      $1[i].raw[j] = (float)PyFloat_AsDouble(o2);
      Py_DECREF(o2);
    }
    Py_DECREF(o);
  }
}

%typemap(freearg) color_hsv_float values[ANY] {
   if ($1) free($1);
}

%typemap(in) color_rgb_float values[ANY] {
  int len = PyObject_Length($input);
  $1 = malloc(sizeof(color_rgb_float) * len);
  int i, j;
  for (i = 0; i < len; i++) {
    PyObject *o = PySequence_GetItem($input, i);
    for (j = 0; j < 3; j++) {
      PyObject *o2 = PySequence_GetItem(o, j);
      $1[i].raw[j] = (float)PyFloat_AsDouble(o2);
      Py_DECREF(o2);
    }
    Py_DECREF(o);
  }
}

%typemap(freearg) color_rgb_float values[ANY] {
   if ($1) free($1);
}

%typemap(out) color_rgb_float {
  $result = PyList_New(3);
  PyList_SetItem($result, 0, PyFloat_FromDouble($1.r));
  PyList_SetItem($result, 1, PyFloat_FromDouble($1.g));
  PyList_SetItem($result, 2, PyFloat_FromDouble($1.b));
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
     PyErr_SetString(PyExc_ValueError, "Expecting a sequence of uint_32s");
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
  if (!convert_iarray_32($input, $1, len)) {
    return NULL;
  }
}

%typemap(freearg) uint32_t values[ANY] {
   if ($1) free($1);
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
#include "rpi_ws281x/ws2811.h"
#include "color_types.h"
#include "led_render.h"
#include "animation_utils.h"
%}

// Process ws2811.h header and export all included functions.
%include "rpi_ws281x/ws2811.h"

// Include render utils
%include "color_types.h"
%include "led_render.h"
%include "animation_utils.h"

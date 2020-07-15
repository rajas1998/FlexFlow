import flexflow.core as ff

from flexflow.keras.models.input_layer import Tensor, Input

class Layer(object):
  __slots__ = ['_ffhandle', '_name', '_layer_type', 'layer_id', \
               'prev_layers', 'next_layers',\
               'input_tensors', 'output_tensors', \
               'input_shape', 'output_shape', 'nb_visited_prev_layers']
  def __init__(self, name, layer_type):
    self._ffhandle = 0
    self._name = name
    self._layer_type = layer_type
    self.layer_id = -1
    self.prev_layers = []
    self.next_layers = []
    self.input_tensors = []
    self.output_tensors = []
    self.input_shape = 0
    self.output_shape = 0
    self.nb_visited_prev_layers = 0
    
  @property
  def name(self):
    return self._name
    
  @property
  def ffhandle(self):
    return self._ffhandle
  
  @ffhandle.setter
  def ffhandle(self, handle):
    self._ffhandle = handle
    
  @property
  def input(self):
    if (len(self.input_tensors) == 1):
      return self.input_tensors[0]
    else:
      return self.input_tensors 
      
  @property
  def output(self):
    if (len(self.output_tensors) == 1):
      return self.output_tensors[0]
    else:
      return self.output_tensors
    
  def reset_layer(self):
    self.reset_connection()
    self.input_shape = 0
    self.output_shape = 0
    self._reset_layer()
    
  def reset_connection(self):
    self.prev_layers.clear()
    self.next_layers.clear()
    self.input_tensors.clear()
    self.output_tensors.clear()
    self.nb_visited_prev_layers = 0
    
  def set_batch_size(self, size):
    lst = list(self.input_shape)
    lst[0] = size
    self.input_shape = tuple(lst)
    lst = list(self.output_shape)
    lst[0] = size
    self.output_shape = tuple(lst)
    
  def _get_weights(self, ffmodel):
    assert self._ffhandle != 0, "handle is not set correctly"
    kernel_parameter = self._ffhandle.get_weight_tensor()
    bias_parameter = self._ffhandle.get_bias_tensor()
    kernel_array = kernel_parameter.get_weights(ffmodel)
    bias_array = bias_parameter.get_weights(ffmodel)
    return (kernel_array, bias_array)
    
  def _set_weights(self, ffmodel, kernel, bias):
    assert self._ffhandle != 0, "handle is not set correctly"
    kernel_parameter = self._ffhandle.get_weight_tensor()
    bias_parameter = self._ffhandle.get_bias_tensor()
    kernel_parameter.set_weights(ffmodel, kernel)
    bias_parameter.set_weights(ffmodel, bias)
    
  def _get_summary_name(self):
    str_name = "{0:25}".format(self._name + " (" + self._layer_type + ")")
    return str_name
    
  def _get_summary_connected_to(self):
    str_name = ""
    for layer in self.prev_layers:
      str_name += "\t%s"%(layer.name)
    return str_name
    
  def _connect_layer_1_input_1_output(self, input_tensor):
    self._calculate_inout_shape(input_tensor)
    output_tensor = Tensor(batch_shape=self.output_shape, dtype=input_tensor.dtype, meta_only=True)
    self._verify_inout_tensor_shape(input_tensor, output_tensor)
    self.input_tensors.append(input_tensor)
    self.output_tensors.append(output_tensor)
    
    output_tensor.set_from_layer(self)
    
    # this is the first layer
    if (isinstance(input_tensor, Input) == True):
      input_tensor.set_to_layer(self)
    # other layers
    else:
      assert input_tensor.from_layer != 0, "[Layer]: check input tensor"
      self.prev_layers.append(input_tensor.from_layer)
      input_tensor.from_layer.next_layers.append(self)

    return output_tensor
    
  def _connect_layer_n_input_1_output(self, input_tensors):
    self._calculate_inout_shape(input_tensors)
    output_tensor = Tensor(batch_shape=self.output_shape, dtype=input_tensors[0].dtype, meta_only=True) 
    self._verify_inout_tensor_shape(input_tensors, output_tensor)
    self.output_tensors.append(output_tensor)
    
    output_tensor.set_from_layer(self)
    
    for tensor in input_tensors:
      self.input_tensors.append(tensor)
      assert tensor.from_layer != 0, "check input tensor"
      self.prev_layers.append(tensor.from_layer)
      tensor.from_layer.next_layers.append(self)
    return output_tensor